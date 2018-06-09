# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CityJsonLoader
                                 A QGIS plugin
 This plugin allows for CityJSON files to be loaded in QGIS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2018-06-08
        git sha              : $Format:%H$
        copyright            : (C) 2018 by 3D Geoinformation
        email                : s.vitalis@tudelft.nl
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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .cityjson_loader_dialog import CityJsonLoaderDialog
import os.path
from cjio import cityjson

class CityJsonLoader:
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
            'CityJsonLoader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = CityJsonLoaderDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CityJSON Loader')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'CityJsonLoader')
        self.toolbar.setObjectName(u'CityJsonLoader')

        self.dlg.browseButton.clicked.connect(self.select_cityjson_file)

    def select_cityjson_file(self):
        filename, _ = QFileDialog.getOpenFileName(self.dlg, "Select CityJSON file", "", "*.json")
        self.dlg.cityjsonPathLineEdit.setText(filename)
        try:
            fstream = open(filename)
            model = cityjson.CityJSON(fstream)
            self.dlg.metadataInfoBox.setPlainText(model.get_info())
        except:
            self.dlg.metadataInfoBox.setPlainText("File could not be loaded")

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
        return QCoreApplication.translate('CityJsonLoader', message)


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
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/cityjson_loader/cityjson_logo.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load CityJSON...'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&CityJSON Loader'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def load_cityjson(self, filename):
        vl = QgsVectorLayer("MultiPolygon", "city_objects", "memory")
        pr = vl.dataProvider()

        pr.addAttributes([QgsField("uid", QVariant.String), QgsField("type", QVariant.String)])
        vl.updateFields()

        file = open(filename)
        city_model = cityjson.CityJSON(file)

        if "crs" in city_model.j["metadata"]:
            vl.setCrs(QgsCoordinateReferenceSystem(city_model.j["metadata"]["crs"]["epsg"]))

        verts = city_model.j["vertices"]
        points = []
        for v in verts:
            points.append(QgsPoint(v[0], v[1], v[2]))

        city_objects = city_model.j["CityObjects"]
        for key, obj in city_objects.items():
            fet = QgsFeature()
            fet.setAttributes([key, obj["type"]])
            geoms = QgsMultiPolygon()
            for geom in obj["geometry"]:
                if "Surface" not in geom["type"]:
                    continue
                for boundary in geom["boundaries"]:
                    g = QgsPolygon()
                    i = 0
                    for ring in boundary:
                        poly = []
                        for index in ring:
                            poly.append(points[index])
                        
                        r = QgsLineString(poly)
                        if i == 0:
                            g.setExteriorRing(r)
                        else:
                            g.addInteriorRing(r)
                        i = 1
                    geoms.addGeometry(g)
            fet.setGeometry(QgsGeometry(geoms))
            pr.addFeature(fet)

        QgsProject.instance().addMapLayer(vl)

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            filename = self.dlg.cityjsonPathLineEdit.text()
            self.load_cityjson(filename)
