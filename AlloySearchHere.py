# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SaveAttributes
                                 A QGIS plugin
 Searches the current map for Alloy items
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-01-24
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Paul Withington
        email                : pwithy@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import QgsProject, Qgis
import urllib
import urllib.request
import json
from math import log, tan, radians, cos, pi, floor, degrees, atan, sinh
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import *
from qgis.utils import iface
import requests
from urllib.request import Request, urlopen
import math

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .AlloySearchHere_dialog import SaveAttributesDialog
import os.path


class SaveAttributes:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SaveAttributes_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Alloy Search Here')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SaveAttributes', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/AlloySearchHere/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Alloy Search Here'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Alloy Search Here'),
                action)
            self.iface.removeToolBarIcon(action)

    def login1(self):
     if self.dlg.lineEditUser.text() == '':
        self.iface.messageBar().pushMessage(
         "Please enter Alloy user name (email) and Alloy password",
         level=Qgis.Success, duration=7)
     elif self.dlg.lineEditUser.text() != '':
      loginurl = "https://api.uk.alloyapp.io/api/session"
      data = {"email":self.dlg.lineEditUser.text(),"password":self.dlg.lineEditPass.text()}
      headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
      try:
       r = requests.post(loginurl, data=json.dumps(data), headers=headers)
       if len(r.content) != 48:
        self.iface.messageBar().pushMessage(
         "User name and or password are incorrect",
         level=Qgis.Success, duration=7)
       elif len(r.content) == 48:
        masterse = json.loads((str(r.content).replace("b'","'")).replace("\'",''))
        customerurl = 'https://api.uk.alloyapp.io/api/customer?&RetrieveLastSeenDate=true&Page=1&PageSize=100'
        headers2 = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': 'Bearer '+masterse['token']}
        requestwh = Request(customerurl, headers=headers2)
        customerdetails = urllib.request.urlopen(requestwh)
        customerdetail = customerdetails.read().decode('utf-8')
        jscustdetail = json.loads(customerdetail)
        customercode = jscustdetail['results'][0]['code']
        newsessionurl = 'https://api.uk.alloyapp.io/api/session/customer/'+customercode+'?'
        data1 = {}
        r2 = requests.post(newsessionurl, data=json.dumps(data1), headers=headers2)
        newsessionr = json.loads((str(r2.content).replace("b'","'")).replace("\'",''))
        self.dlg.lineEdit.setText(newsessionr['token'])
        self.dlg.label_7.setText('Login Successful')
        semail = QgsSettings()
        semail.setValue("emailadd/username", self.dlg.lineEditUser.text())
      except:
       self.iface.messageBar().pushMessage(
        "Connection failed check proxy",
        level=Qgis.Success, duration=7)

    def GetAlloyLayers(self):
     if self.dlg.label_7.text() == 'Not Logged In':
        self.iface.messageBar().pushMessage(
         "Please log in",
         level=Qgis.Success, duration=7)
     elif self.dlg.label_7.text() != 'Not Logged In':
       self.dlg.comboBoxLayers.clear()
       APIkey = self.dlg.lineEdit.text()
       APIheader = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': 'Bearer '+APIkey}
       if self.dlg.horizontalSlider.value() == 0:
        Lrtype = 'network'
       elif self.dlg.horizontalSlider.value() == 1:
        Lrtype = 'cluster'
       userlayerurl = 'https://api.uk.alloyapp.io/api/layer?Context=Customer&Visualisations='+Lrtype+'&PageSize=100'
       userlayerurlr = Request(userlayerurl, headers=APIheader)
       jresp = urllib.request.urlopen(userlayerurlr)
       rawresp = jresp.read().decode('utf-8')
       avLayer = json.loads(rawresp)
       testtable= {"name": [],"code": []}
       testtable['name'] = [results['layer']['name'] for results in avLayer['results']]
       testtable['code'] = [results['layer']['code'] for results in avLayer['results']]
       self.dlg.comboBoxLayers.addItems(testtable['name'])
       scale=iface.mapCanvas().scale()
       dpi=iface.mainWindow().physicalDpiX()
       maxScalePerPixel = 156543.04
       inchesPerMeter = 39.37
       zoomlevel = int(round(math.log( ((dpi* inchesPerMeter * maxScalePerPixel) / scale), 2 ), 0))
       self.dlg.labelczoom.setText(str(zoomlevel))

    def SeHere(self):
     if self.dlg.label_7.text() == 'Not Logged In':
        self.iface.messageBar().pushMessage(
         "Please log in",
         level=Qgis.Success, duration=7)
     elif self.dlg.label_7.text() != 'Not Logged In':
      APIkey = self.dlg.lineEdit.text()
      APIheader = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': 'Bearer '+APIkey}
      if self.dlg.horizontalSlider.value() == 0:
       Lrtype = 'network'
      elif self.dlg.horizontalSlider.value() == 1:
       Lrtype = 'cluster'
      userlayerurl = 'https://api.uk.alloyapp.io/api/layer?Context=Customer&Visualisations='+Lrtype+'&PageSize=100'
      userlayerurlr = Request(userlayerurl, headers=APIheader)
      jresp = urllib.request.urlopen(userlayerurlr)
      rawresp = jresp.read().decode('utf-8')
      avLayer = json.loads(rawresp)
      testtable= {"name": [],"code": []}
      testtable['name'] = [results['layer']['name'] for results in avLayer['results']]
      testtable['code'] = [results['layer']['code'] for results in avLayer['results']]
      self.dlg.labelCsLayerID.setText(testtable['code'][self.dlg.comboBoxLayers.currentIndex()])
      Starturl = 'https://api.uk.alloyapp.io/api/layer/'
      LayerS = testtable['code'][self.dlg.comboBoxLayers.currentIndex()]+'/'
      crsSrc = QgsCoordinateReferenceSystem(iface.mapCanvas().mapSettings().destinationCrs().authid())
      crsDest = QgsCoordinateReferenceSystem("EPSG:4326")
      transformContext = QgsProject.instance().transformContext()
      xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
      if self.dlg.horizontalSlider.value() == 0:
       mpzoom = '15'+'/'
       zoom = 15
       min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x()-0.01,iface.mapCanvas().extent().center().y()))
       mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))-1) + '/'
       mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2))+'/'
      elif self.dlg.horizontalSlider.value() == 1:
       mpzoom = '16'+'/'
       zoom = 16
       min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
       mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))-1) + '/'
       mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2)-1)+'/'
      type = Lrtype+'?'
      LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
      LayerURLr = Request(LayerURL, headers=APIheader)
      json_response = urllib.request.urlopen(LayerURLr)
      rawresponse = json_response.read().decode('utf-8')
      testres = "'"+rawresponse+"'"
      testnul = "'"+'{"results":[]}'+"'"
      if testres != testnul:
       jload = json.loads(rawresponse.replace("\'",''))
       tempc = {'results':[]}
       for r in jload['results']:
        tempc['results'].append(r)
       #second tile
       if self.dlg.horizontalSlider.value() == 0:
        mpzoom = '15'+'/'
        zoom = 15
        min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
        mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))) + '/'
        mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2))+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
        mpzoom = '15'+'/'
        zoom = 15
        min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
        mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))) + '/'
        mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2)-1)+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
        mpzoom = '15'+'/'
        zoom = 15
        min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
        mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))-1) + '/'
        mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2)-1)+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
       elif self.dlg.horizontalSlider.value() == 1:
        mpzoom = '16'+'/'
        zoom = 16
        min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
        mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))) + '/'
        mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2)-1)+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
         mpzoom = '16'+'/'
         zoom = 16
         min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
         mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))) + '/'
         mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2))+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
         mpzoom = '16'+'/'
         zoom = 16
         min = xform.transform(QgsPointXY(iface.mapCanvas().extent().center().x(),iface.mapCanvas().extent().center().y()))
         mpx = str((round(pow(2, zoom)*((min.x()) + 180) / 360))-1) + '/'
         mpy = str(round(pow(2, zoom)*(1 - log(tan(radians(min.y())) + 1/cos((radians(min.y())))) / pi) / 2))+'/'
        LayerURL = Starturl+LayerS+mpx+mpy+mpzoom+type
        LayerURLr = Request(LayerURL, headers=APIheader)
        json_response2 = urllib.request.urlopen(LayerURLr)
        rawresponse2 = json_response2.read().decode('utf-8')
        jload2 = json.loads(rawresponse2.replace("\'",''))
        for r in jload2['results']:
         tempc['results'].append(r)
       #for map
       gej = {"type": "FeatureCollection","features": []}
       gej['features'] = tempc['results']
       for feature in gej['features']:
       	del feature['id']
       
       ercorrect = str(gej).replace("'",'"')
       vlayer = QgsVectorLayer(ercorrect, testtable['name'][self.dlg.comboBoxLayers.currentIndex()], "ogr")
       QgsProject.instance().addMapLayer(vlayer)
      elif testres == testnul:
        self.iface.messageBar().pushMessage(
         "No items in view",
         level=Qgis.Success, duration=7)

    def caljson(self):
        dis = 0
        try:
         feats = iface.mapCanvas().currentLayer().selectedFeatures()
         if iface.mapCanvas().currentLayer().selectedFeatureCount() == 0:
          self.iface.messageBar().pushMessage(
          "No item selected",
          level=Qgis.Success, duration=7)
         elif iface.mapCanvas().currentLayer().selectedFeatureCount() != 0:
          geomSingleType = QgsWkbTypes.isSingleType(feats[0].geometry().wkbType())
          if geomSingleType:
             if feats[0].geometry().type() == 1:
               crsSrc = QgsCoordinateReferenceSystem(iface.mapCanvas().currentLayer().crs().authid())
               crsDest = QgsCoordinateReferenceSystem("EPSG:4326")
               transformContext = QgsProject.instance().transformContext()
               xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
               fstline = ''
               feats = iface.mapCanvas().currentLayer().selectedFeatures()
               fstline = feats[0].geometry().asPolyline()
               poly_reproj = fstline
               for i, point in enumerate(fstline):
                pt = xform.transform(point)
                poly_reproj[i] = pt
               feature = QgsFeature()
               feature.setGeometry(QgsGeometry.fromPolylineXY(poly_reproj))
               dis = 1
             elif feats[0].geometry().type() == 2:
              crsSrc = QgsCoordinateReferenceSystem(iface.mapCanvas().currentLayer().crs().authid())
              crsDest = QgsCoordinateReferenceSystem("EPSG:4326")
              transformContext = QgsProject.instance().transformContext()
              xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
              fstpoly = ''
              feats = iface.mapCanvas().currentLayer().selectedFeatures()
              fstpoly = feats[0].geometry().asPolygon()
              poly_reproj = fstpoly
              for i, point in enumerate(fstpoly[0]):
               pt = xform.transform(point)
               poly_reproj[0][i] = pt
              feature = QgsFeature()
              feature.setGeometry(QgsGeometry.fromPolygonXY(poly_reproj))
              dis = 1
             elif feats[0].geometry().type() == 0:
              crsSrc = QgsCoordinateReferenceSystem(iface.mapCanvas().currentLayer().crs().authid())
              crsDest = QgsCoordinateReferenceSystem("EPSG:4326")
              transformContext = QgsProject.instance().transformContext()
              xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)
              fstline = ''
              feats = iface.mapCanvas().currentLayer().selectedFeatures()
              fstline = feats[0].geometry().asPoint()
              poly_reproj = fstline
              pt = xform.transform(fstline)
              feature = QgsFeature()
              feature.setGeometry(QgsGeometry.fromPointXY(pt))
              dis = 1
             else:
              self.iface.messageBar().pushMessage(
              "unknown geometry type",
              level=Qgis.Success, duration=7)
          else:
           self.iface.messageBar().pushMessage(
           "Item selected is type multi",
           level=Qgis.Success, duration=7)
        except:
         self.iface.messageBar().pushMessage(
         "Please select a vector item",
         level=Qgis.Success, duration=7)
        if dis != 0:
         self.dlg.textBrowser.setText(feature.geometry().asJson())

    def GetAlloyItem(self):
     if self.dlg.label_7.text() == 'Not Logged In':
        self.iface.messageBar().pushMessage(
         "Please log in",
         level=Qgis.Success, duration=7)
     elif self.dlg.label_7.text() != 'Not Logged In':
        APIkey = self.dlg.lineEdit.text()
        headers2 = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': 'Bearer '+APIkey}
        try:
         feats = iface.mapCanvas().currentLayer().selectedFeatures()
         if iface.mapCanvas().currentLayer().selectedFeatureCount() == 0:
          self.iface.messageBar().pushMessage(
          "No item selected",
          level=Qgis.Success, duration=7)
         elif iface.mapCanvas().currentLayer().selectedFeatureCount() != 0:
          try:
           if len(feats[0]['designCode']) >= 1:
            customerurl = 'https://api.uk.alloyapp.io/api/item/'+feats[0]['itemid']+'?'
            customerurlr = Request(customerurl, headers=headers2)
            customerdetails = urllib.request.urlopen(customerurlr)
            customerdetail = customerdetails.read().decode('utf-8')
            jscustdetail = json.loads(customerdetail)
            AlloyItem= {"attribute": [],"value": []}
            AlloyItemB = ''
            for item in jscustdetail['item']['attributes']:
             if item['attributeCode'] == 'attributes_itemsGeometry':
              AlloyItem = AlloyItem
             else:
              #AlloyItemB += str(item['attributeCode'])+'\n'
              AlloyItemB += str(item['value'])+'\n'
              #AlloyItem['value'].append(item['value'])
            self.dlg.label_19.setText(AlloyItemB)
          except:
           self.iface.messageBar().pushMessage(
           "The selected item is not from the search here function",
           level=Qgis.Success, duration=7)
        except:
          self.iface.messageBar().pushMessage(
          "Please select a vector item",
          level=Qgis.Success, duration=7)


    def GetAlloyLayer(self):
     if self.dlg.label_7.text() == 'Not Logged In':
        self.iface.messageBar().pushMessage(
         "Please log in",
         level=Qgis.Success, duration=7)
     elif self.dlg.label_7.text() != 'Not Logged In':
        ItemErMes = 0
        LoadErMes = 0
        APIkey = self.dlg.lineEdit.text()
        page = 1
        if self.dlg.lineEdit_2.text() == '':
         self.dlg.lineEdit_2.setText(str(self.plugin_dir).replace('\\','/')+'/temp.GeoJson')
        try:
         feats = iface.mapCanvas().currentLayer().selectedFeatures()
         if iface.mapCanvas().currentLayer().selectedFeatureCount() == 0:
          self.iface.messageBar().pushMessage(
          "No item selected",
          level=Qgis.Success, duration=7)
         elif iface.mapCanvas().currentLayer().selectedFeatureCount() != 0:
          progr = 5
          self.dlg.progressBar.setValue(progr)
          try:
           if len(feats[0]['designCode']) >= 1:
            staturl = 'https://api.uk.alloyapp.io/api/aqs/statistics?'
            stataqs = '{"aqs":{"type":"StatisticsAggregation","properties":{"dodiCode":"'+feats[0]['designCode']+'","collectionCode":["Live"],"aggregationType":"Count"}}}'
            aqsall = '{"aqs":{"type":"Join","properties":{"attributes":["all"],"collectionCode":["Live"],"dodiCode":"'+feats[0]['designCode']+'","joinAttributes":[]},"children":[{"type":"Exists","children":[{"type":"Attribute","properties":{"attributeCode":"attributes_itemsGeometry"}}]}]},"parameterValues":[]}'
            aqs = '{"aqs":{"type":"Join","properties":{"attributes":["attributes_itemsTitle","attributes_itemsSubtitle","attributes_itemsGeometry"],"collectionCode":["Live"],"dodiCode":"'+feats[0]['designCode']+'","joinAttributes":[]},"children":[{"type":"Exists","children":[{"type":"Attribute","properties":{"attributeCode":"attributes_itemsGeometry"}}]}]},"parameterValues":[]}'
            statdata  = json.loads(stataqs)
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': 'Bearer '+APIkey}
            tempc = {'results':[]}
            sr = requests.post(staturl, data=json.dumps(statdata), headers=headers)
            srjload = json.loads((str(sr.content).replace("b'","'")).replace("\'",''))
            statvalue = srjload['results'][0]['value']['value']
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("You are about to download "+str(statvalue)+" records, please be patient")
            msgBox.setWindowTitle("About to download lots of data")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
             while True:
              url = "https://api.uk.alloyapp.io/api/aqs/join?Page="+str(page)+"&PageSize=100&"
              if self.dlg.horizontalSlider_2.value() == 0:
               data = json.loads(aqs)
              elif self.dlg.horizontalSlider.value() == 1:
               data = json.loads(aqsall)
              r = requests.post(url, data=json.dumps(data), headers=headers)
              if r.status_code == 200:
               try:
                jload = json.loads(((str(r.content).replace("b'","'")).replace("\'",'')).replace("\\",''))
                for item in jload['results']:
                 tempc['results'].append(item)
               except:
                LoadErMes = LoadErMes + 1
              page = page + 1
              progr = progr+1
              self.dlg.progressBar.setValue(progr)
              if r.status_code != 200:
               break
             gej = {"type": "FeatureCollection","features": []}
             for ritem in tempc['results']:
              temp = 1
              gejitem = {"type": "Feature","geometry": [],"properties": {}}
              for i in ritem['attributes']:
               if i['attributeCode'] == "attributes_itemsGeometry":
                gejitem['geometry'] = i['value']
               if i['attributeCode'] != "attributes_itemsGeometry":
                if temp == 1:
                 attname = i['attributeCode']
                 attvalue = i['value']
                 temp = {attname:str(attvalue)}
                else:
                  attname = i['attributeCode']
                attvalue = i['value']
                try:
                 temp = json.loads(str((str(temp)[:-1]+', '''+"'"+str(attname)+"'"+':'''+"'"+str(attvalue)+"'}")).replace("'",'"'))
                except:
                 ItemErMes = ItemErMes + 1
              gejitem['properties'] = temp
              gej['features'].append(gejitem)
              if progr <= 90:
               progr = progr + 0.01
               self.dlg.progressBar.setValue(progr)
             file = open(self.dlg.lineEdit_2.text(),'w')
             file.write(str(gej).replace("'",'"'))
             file.close
             #vlayer = QgsVectorLayer(str(self.plugin_dir).replace('\\','/')+'/temp.GeoJson', "Layer", "ogr")
             #QgsProject.instance().addMapLayer(vlayer)
             self.iface.messageBar().pushMessage(
             'downloaded to temp.GeoJson<a href="url">'+self.dlg.lineEdit_2.text()+'/</a>',
             level=Qgis.Success, duration=12)
             if ItemErMes >= 1:
              self.iface.messageBar().pushMessage(
              "some attributes lost due to problem characters in text fields",
              level=Qgis.Success, duration=7)
             if LoadErMes >= 1:
              self.iface.messageBar().pushMessage(
              LoadErMes+"00 features lost due to problem characters in text fields",
              level=Qgis.Success, duration=7)
            if returnValue == QMessageBox.Cancel:
             self.iface.messageBar().pushMessage(
             "Cancel clicked",
             level=Qgis.Success, duration=7)
          except:
           self.iface.messageBar().pushMessage(
           "The selected item is not from the search here function",
           level=Qgis.Success, duration=7)
        except:
          self.iface.messageBar().pushMessage(
          "Please select a vector item",
          level=Qgis.Success, duration=7)
        self.dlg.progressBar.setValue(0)

    def setpath(self):
     filename1 = QFileDialog.getSaveFileName(filter='*.GeoJson')
     self.dlg.lineEdit_2.setText(filename1[0])

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SaveAttributesDialog()
            self.dlg.pushButtonlogin.clicked.connect(self.login1)
            self.dlg.pushButtonGetLayers.clicked.connect(self.GetAlloyLayers)
            self.dlg.pushButtonSeHere.clicked.connect(self.SeHere)
            self.dlg.pushButtonCalc.clicked.connect(self.caljson)
            self.dlg.pushButtonGetDetails.clicked.connect(self.GetAlloyItem)
            self.dlg.pushButtonGetFullLayer.clicked.connect(self.GetAlloyLayer)
            self.dlg.pushButtonfolder.clicked.connect(self.setpath)


        # show the dialog
        self.dlg.show()
        try:
         semail = QgsSettings()
         loaduser = semail.value("emailadd/username", "default text")
         self.dlg.lineEditUser.setText(loaduser)
         self.dlg.lineEdit_2.setText(str(self.plugin_dir).replace('\\','/')+'/temp.GeoJson')
        except:
         semail = QgsSettings()
        result = self.dlg.exec_()
        # See if OK was pressed
        #print('ok pressed')
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

