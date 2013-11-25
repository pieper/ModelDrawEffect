import os
import unittest
from __main__ import vtk, qt, ctk, slicer
import EditorLib
from EditorLib.EditOptions import HelpButton
from EditorLib.EditOptions import EditOptions
from EditorLib import EditUtil
from EditorLib import LabelEffect

#
# The Editor Extension itself.
#
# This needs to define the hooks to be come an editor effect.
#

#
# ModelDrawEffectOptions - see LabelEffect, EditOptions and Effect for superclasses
#

class ModelDrawEffectOptions(EditorLib.LabelEffectOptions):
  """ ModelDrawEffect-specfic gui
  """

  def __init__(self, parent=0):
    super(ModelDrawEffectOptions,self).__init__(parent)

    # self.attributes should be tuple of options:
    # 'MouseTool' - grabs the cursor
    # 'Nonmodal' - can be applied while another is active
    # 'Disabled' - not available
    self.attributes = ('MouseTool')
    self.displayName = 'ModelDrawEffect Effect'

  def __del__(self):
    super(ModelDrawEffectOptions,self).__del__()

  def create(self):
    super(ModelDrawEffectOptions,self).create()
    self.apply = qt.QPushButton("Apply", self.frame)
    self.apply.setToolTip("Apply the extension operation")
    self.frame.layout().addWidget(self.apply)
    self.widgets.append(self.apply)

    HelpButton(self.frame, "This is a sample with no real functionality.")

    self.connections.append( (self.apply, 'clicked()', self.onApply) )

    # Add vertical spacer
    self.frame.layout().addStretch(1)

  def destroy(self):
    super(ModelDrawEffectOptions,self).destroy()

  # note: this method needs to be implemented exactly as-is
  # in each leaf subclass so that "self" in the observer
  # is of the correct type
  def updateParameterNode(self, caller, event):
    node = EditUtil.EditUtil().getParameterNode()
    if node != self.parameterNode:
      if self.parameterNode:
        node.RemoveObserver(self.parameterNodeTag)
      self.parameterNode = node
      self.parameterNodeTag = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.updateGUIFromMRML)

  def setMRMLDefaults(self):
    super(ModelDrawEffectOptions,self).setMRMLDefaults()

  def updateGUIFromMRML(self,caller,event):
    self.disconnectWidgets()
    super(ModelDrawEffectOptions,self).updateGUIFromMRML(caller,event)
    self.connectWidgets()

  def onApply(self):
    print('This is just an example - nothing here yet')

  def updateMRMLFromGUI(self):
    if self.updatingGUI:
      return
    disableState = self.parameterNode.GetDisableModifiedEvent()
    self.parameterNode.SetDisableModifiedEvent(1)
    super(ModelDrawEffectOptions,self).updateMRMLFromGUI()
    self.parameterNode.SetDisableModifiedEvent(disableState)
    if not disableState:
      self.parameterNode.InvokePendingModifiedEvent()


#
# ModelDrawEffectTool
#

class ModelDrawEffectTool(LabelEffect.LabelEffectTool):
  """
  One instance of this will be created per-view when the effect
  is selected.  It is responsible for implementing feedback and
  label map changes in response to user input.
  This class observes the editor parameter node to configure itself
  and queries the current view for background and label volume
  nodes to operate on.
  """

  def __init__(self, sliceWidget):
    super(ModelDrawEffectTool,self).__init__(sliceWidget)
    # create a logic instance to do the non-gui work
    self.logic = ModelDrawEffectLogic(self.sliceWidget.sliceLogic())

  def cleanup(self):
    super(ModelDrawEffectTool,self).cleanup()

  def processEvent(self, caller=None, event=None):
    """
    handle events from the render window interactor
    """

    # let the superclass deal with the event if it wants to
    if super(ModelDrawEffectTool,self).processEvent(caller,event):
      return

    if event == "LeftButtonPressEvent":
      xy = self.interactor.GetEventPosition()
      sliceLogic = self.sliceWidget.sliceLogic()
      logic = ModelDrawEffectLogic(sliceLogic)
      logic.apply(xy)
      print("NEW!!!! Got a %s at %s in %s" % (event,str(xy),self.sliceWidget.sliceLogic().GetSliceNode().GetName()))
      self.abortEvent(event)
    else:
      pass

    # events from the slice node
    if caller and caller.IsA('vtkMRMLSliceNode'):
      # here you can respond to pan/zoom or other changes
      # to the view
      pass


#
# ModelDrawEffectLogic
#

class ModelDrawEffectLogic(LabelEffect.LabelEffectLogic):
  """
  This class contains helper methods for a given effect
  type.  It can be instanced as needed by an ModelDrawEffectTool
  or ModelDrawEffectOptions instance in order to compute intermediate
  results (say, for user feedback) or to implement the final
  segmentation editing operation.  This class is split
  from the ModelDrawEffectTool so that the operations can be used
  by other code without the need for a view context.
  """

  def __init__(self,sliceLogic):
    self.sliceLogic = sliceLogic

  def apply(self,xy):
    pass


#
# The ModelDrawEffect class definition
#

class ModelDrawEffectExtension(LabelEffect.LabelEffect):
  """Organizes the Options, Tool, and Logic classes into a single instance
  that can be managed by the EditBox
  """

  def __init__(self):
    # name is used to define the name of the icon image resource (e.g. ModelDrawEffect.png)
    self.name = "ModelDrawEffect"
    # tool tip is displayed on mouse hover
    self.toolTip = "Paint: circular paint brush for label map editing"

    self.options = ModelDrawEffectOptions
    self.tool = ModelDrawEffectTool
    self.logic = ModelDrawEffectLogic


#
# ModelDrawEffect
#

class ModelDrawEffect:
  """
  This class is the 'hook' for slicer to detect and recognize the extension
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "Editor ModelDraw Effect"
    parent.categories = ["Developer Tools.Editor Extensions"]
    parent.contributors = ["Steve Pieper (Isomics)"] # insert your name in the list
    parent.helpText = """
    Example of an editor extension.  No module interface here, only in the Editor module
    """
    parent.acknowledgementText = """
    This editor extension was developed by
    Steve Pieper, Isomics, Inc.
    and was partially funded by NIH grant 3P41RR013218 and by Novartis.
    """

    parent.hidden = False


    # Add this extension to the editor's list for discovery when the module
    # is created.  Since this module may be discovered before the Editor itself,
    # create the list if it doesn't already exist.
    try:
      slicer.modules.editorExtensions
    except AttributeError:
      slicer.modules.editorExtensions = {}
    slicer.modules.editorExtensions['ModelDrawEffect'] = ModelDrawEffectExtension

#
# ModelDrawEffectWidget
#

class ModelDrawEffectWidget:
  def __init__(self, parent = None):
    self.parent = parent

    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

    self.overlaysByLayoutName = None
    self.htmlFormat = """
    <HEAD></HEAD> <BODY>
      <div id="annotation"> <p style ="position: absolute;
                display: inline;
                top: 5;
                left: 5;
                border: 2px solid #777;
                padding: 5px;
                background-color: #fff;
                opacity: 0.70" >
                Annotation Text %d</p>
      </div> </BODY>
    """

  def cleanup(self):
    pass

  def setup(self):
    """For development, add a reloadable section"""
    #
    # Add Overlays area
    #
    overlayCollapsibleButton = ctk.ctkCollapsibleButton()
    overlayCollapsibleButton.text = "Overlays"
    self.layout.addWidget(overlayCollapsibleButton)
    overlayFormLayout = qt.QFormLayout(overlayCollapsibleButton)

    self.overlaysCheck = qt.QCheckBox()
    overlayFormLayout.addRow("Overlays", self.overlaysCheck)
    self.overlaysCheck.connect("toggled(bool)", self.onOverlaysToggled)

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "ModelDrawEffect Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and run specific tests
    scenarios = ("ThreeD","Slice","All")
    for scenario in scenarios:
      button = qt.QPushButton("Reload and Test %s" % scenario)
      button.toolTip = "Reload this module and then run the %s self test." % scenario
      reloadFormLayout.addWidget(button)
      button.connect('clicked()', lambda s=scenario: self.onReloadAndTest(scenario=s))

  def enter(self):
    pass

  def exit(self):
    pass

  def onOverlaysToggled(self):
    if self.overlaysCheck.checked:
      self.overlaysByLayoutName = {}
      # get new slice nodes
      layoutManager = slicer.app.layoutManager()
      sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
      for nodeIndex in xrange(sliceNodeCount):
        # find the widget for each node in scene
        sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
        layoutName = sliceNode.GetLayoutName()
        sliceWidget = layoutManager.sliceWidget(layoutName)
        if sliceWidget:
          # add obserservers and keep track of tags
          overlay = SliceWebOverlay(sliceWidget.sliceView())
          overlay.setHtml(self.htmlFormat % nodeIndex)
          self.overlaysByLayoutName[layoutName] = overlay
    else:
      for layoutName,overlay in self.overlaysByLayoutName.iteritems():
        overlay.release()
      self.overlaysByLayoutName = None


  def onReload(self,moduleName="ModelDrawEffect"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

    # special for Editor Effects - register as the new implementation of effect
    slicer.modules.editorExtensions['ModelDrawEffect'] = ModelDrawEffectExtension

  def onReloadAndTest(self,moduleName="ModelDrawEffect",scenario=None):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest(scenario=scenario)
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


class SliceWebOverlay:

  def __init__(self,sliceView):
    self.observerTags = []
    self.sliceView = sliceView
    self.addWebActor()

  def release(self):
    # remove observers and reset
    self.removeWebActor()
    for observee,tag in self.observerTags:
      observee.RemoveObserver(tag)
    self.observerTags = []

  def setHtml(self,html):
    self.webView.setHtml(html)

  def onLoadFinished(self,worked):
    self.qImage.fill(0)
    self.webView.render(self.qImage)
    utils = slicer.qMRMLUtils()
    utils.qImageToVtkImageData(self.qImage,self.vtkImage)
    self.imageActor.SetInput(self.vtkImage)
    self.sliceView.scheduleRender()

  def processEvent(self, caller=None, event=None):
    htmlFormat = """
    <HEAD></HEAD> <BODY>
      <div id="annotation"> <p style ="position: absolute;
                display: inline;
                top: 5;
                left: 5;
                border: 2px solid #777;
                padding: 5px;
                background-color: #fff;
                opacity: 0.70" >
                %s</p>
      </div> </BODY>
    """
    pos = self.style.GetEventPosition()
    s = 'got %s from %s at %s' % (event,caller.GetClassName(),str(pos))
    s +='<br>size is %d by %d' % (self.sliceView.width,self.sliceView.height)
    self.setHtml(htmlFormat % s)
    pass

  def addWebActor(self):
    self.webView = qt.QWebView()
    self.webView.setWindowFlags(0x800)
    self.webView.setStyleSheet('background:transparent;')

    w, h = self.sliceView.width,self.sliceView.height
    self.qImage = qt.QImage(w, h, qt.QImage.Format_ARGB32)
    self.vtkImage = vtk.vtkImageData()

    self.mapper = vtk.vtkImageMapper()
    self.mapper.SetColorLevel(128)
    self.mapper.SetColorWindow(255)
    self.mapper.SetInput(self.vtkImage)
    self.actor2D = vtk.vtkActor2D()
    self.actor2D.SetMapper(self.mapper)

    self.imageActor = vtk.vtkImageActor()
    #self.imageActor.SetPosition(0,-1000,0)
    self.renderWindow = self.sliceView.renderWindow()
    self.renderer = self.renderWindow.GetRenderers().GetItemAsObject(0)
    self.renderer.AddActor2D(self.actor2D)

    globals()['slicer'].ia = self.imageActor

    self.webView.connect('loadFinished(bool)', lambda worked : self.onLoadFinished(worked) )
    #self.webView.page().connect('repaintRequested(QRect)', lambda rect : onLoadFinished(rect, self.webView, self.qImage) )

    self.style = self.sliceView.interactor()
    events = ("ModifiedEvent", "MouseMoveEvent", "EnterEvent", "LeaveEvent",)
    for event in events:
      tag = self.style.AddObserver(event, self.processEvent)
      self.observerTags.append([self.style,tag])

  def removeWebActor(self):
    self.renderer.RemoveActor(self.actor2D)
    del(self.webView)
    self.webView = None
    self.sliceView.scheduleRender()


class ModelDrawEffectTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def __init__(self):
    self.webView = None
    self.htmlFormat = """
    <HEAD></HEAD> <BODY>
      <div id="annotation"> <p style ="position: absolute;
                display: inline;
                top: 5;
                left: 5;
                border: 2px solid #777;
                padding: 5px;
                background-color: #fff;
                opacity: 0.70" >
                Annotation Text %d</p>
      </div> </BODY>
    """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self,scenario=None):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    if scenario == "ThreeD":
      self.test_ModelDrawEffect1()
    elif scenario == "Slice":
      self.test_ModelDrawEffect2()
    else:
      self.test_ModelDrawEffect1()
      self.test_ModelDrawEffect2()

  def onLoadFinished(self,worked):
    self.qImage.fill(0)
    self.webView.render(self.qImage)
    utils = slicer.qMRMLUtils()
    utils.qImageToVtkImageData(self.qImage,self.vtkImage)
    self.imageActor.SetInput(self.vtkImage)
    self.threeDView.scheduleRender()

  def addWebActor(self):
    self.webView = qt.QWebView()
    self.webView.setWindowFlags(0x800)
    self.webView.setStyleSheet('background:transparent;')

    self.qImage = qt.QImage(1000,1000, qt.QImage.Format_ARGB32)
    self.vtkImage = vtk.vtkImageData()

    lm = slicer.app.layoutManager()
    redWidget = lm.sliceWidget('Red')
    self.threeDView = lm.threeDWidget(0).threeDView()

    self.imageActor = vtk.vtkImageActor()
    self.imageActor.SetPosition(0,-1000,0)
    self.renderWindow = self.threeDView.renderWindow()
    self.renderer = self.renderWindow.GetRenderers().GetItemAsObject(0)
    self.renderer.AddActor(self.imageActor)

    globals()['slicer'].modules.ModelDrawEffectWidget.ia = self.imageActor

    self.webView.connect('loadFinished(bool)', lambda worked : self.onLoadFinished(worked) )
    #self.webView.page().connect('repaintRequested(QRect)', lambda rect : onLoadFinished(rect, self.webView, self.qImage) )

  def removeWebActor(self):
    self.renderer.RemoveActor(self.imageActor)
    del(self.webView)
    self.webView = None
    self.threeDView.scheduleRender()

  def test_ModelDrawEffect1(self):
    """
    This tests basic landmarking with two volumes
    """

    self.delayDisplay("Starting test_ModelDrawEffect1")
    #
    # first, get some data
    #
    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    mrHead = sampleDataLogic.downloadMRHead()
    self.delayDisplay('data set loaded')

    w = slicer.modules.ModelDrawEffectWidget

    qt.QWebSettings.globalSettings().setAttribute(qt.QWebSettings.DeveloperExtrasEnabled, True)

    self.delayDisplay('adding web actor')
    if not self.webView:
      self.addWebActor()

    self.threeDView.lookFromAxis(3,200)

    self.delayDisplay('setting URL')
    self.webView.setUrl(qt.QUrl('http://bl.ocks.org/1703449'))
    self.delayDisplay('displaying URL',5000)


    self.delayDisplay('displaying html',2000)
    self.webView.setHtml(self.htmlFormat)

    for i in xrange(20):
      self.webView.setHtml(self.htmlFormat % i)
      self.renderWindow.Render()
      self.delayDisplay('displaying html %d' % i,10)

    self.removeWebActor()

    self.delayDisplay('test_ModelDrawEffect1 passed!')


  def test_ModelDrawEffect2(self):

    self.delayDisplay('test_ModelDrawEffect2 running!',500)

    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    mrHead = sampleDataLogic.downloadMRHead()

    globals()['slicer'].ov = []

    overlaysByLayoutName = {}
    # get new slice nodes
    layoutManager = slicer.app.layoutManager()
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in xrange(sliceNodeCount):
      # find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      layoutName = sliceNode.GetLayoutName()
      self.delayDisplay('adding to %s' % layoutName,200)
      sliceWidget = layoutManager.sliceWidget(layoutName)
      if sliceWidget:
        # add obserservers and keep track of tags
        overlay = SliceWebOverlay(sliceWidget.sliceView())
        overlay.setHtml(self.htmlFormat % nodeIndex)
        overlaysByLayoutName[layoutName] = overlay

        globals()['slicer'].ov.append(overlay)

    self.delayDisplay('Check them out!')
    
    for layoutName,overlay in overlaysByLayoutName.iteritems():
      overlay.release()
    overlaysByLayoutName = None

    self.delayDisplay('test_ModelDrawEffect2 passed!')
