from Components.ActionMap import HelpableActionMap
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigSubList, ConfigInteger, ConfigYesNo, ConfigText, ConfigNothing, ConfigDirectory
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import BoxInfo
from Screens.Setup import Setup
from Tools.BoundFunction import boundFunction
from Tools.Directories import isPluginInstalled
from . import _, PluginLanguageDomain


def initConnection(index):
	config.plugins.e2jellyfinclient.connections.append(ConfigSubsection())
	config.plugins.e2jellyfinclient.connections[index].name = ConfigText(default="Server", visible_width=50, fixed_size=False)
	config.plugins.e2jellyfinclient.connections[index].ip = ConfigText(default="https://ip")
	config.plugins.e2jellyfinclient.connections[index].port = ConfigInteger(default=8096, limits=(1, 65555))
	config.plugins.e2jellyfinclient.connections[index].user = ConfigText(default="user", visible_width=50, fixed_size=False)
	config.plugins.e2jellyfinclient.connections[index].password = ConfigText(default="password", visible_width=50, fixed_size=False)
	return config.plugins.e2jellyfinclient.connections[index]


def initConfig():
	config.plugins.e2jellyfinclient = ConfigSubsection()
	config.plugins.e2jellyfinclient.add_to_mainmenu = ConfigYesNo(default=False)
	config.plugins.e2jellyfinclient.add_to_extensionmenu = ConfigYesNo(default=False)
	config.plugins.e2jellyfinclient.conretries = ConfigInteger(default=5, limits=(5, 20))
	config.plugins.e2jellyfinclient.con_timeout = ConfigInteger(default=2, limits=(1, 20))
	config.plugins.e2jellyfinclient.read_con_timeout = ConfigInteger(default=10, limits=(2, 20))
	config.plugins.e2jellyfinclient.nothing = ConfigNothing()
	config.plugins.e2jellyfinclient.connectioncount = ConfigInteger(0)
	config.plugins.e2jellyfinclient.activeconnection = ConfigInteger(0)
	config.plugins.e2jellyfinclient.connections = ConfigSubList()
	choicelist = [(i, "%d ms" % i) for i in range(50, 1500, 50)]  # noqa: F821
	config.plugins.e2jellyfinclient.changedelay = ConfigSelection(default=150, choices=choicelist)
	isServiceAppInstalled = isPluginInstalled("ServiceApp")
	play_system_choices = [("4097", "HiPlayer" if BoxInfo.getItem("mediaservice") == "servicehisilicon" else "GStreamer")]
	if isServiceAppInstalled:
		play_system_choices.append(("5002", "Exteplayer3"))
	config.plugins.e2jellyfinclient.play_system = ConfigSelection(default="4097", choices=play_system_choices)
	subs_encoddings_choices = [("latin1", "Latin"), ("windows-1251", "Cyrillic"), ("Shift_JIS", "Japanese/日本語"), ("Big5", "Chinese (Traditional)/繁體中文"), ("GB2312", "Chinese (Simplified)/简体中文"), ("Windows-1256", "Arabic/العربية")]
	config.plugins.e2jellyfinclient.encodding_nonutf_subs = ConfigSelection(default="latin1", choices=subs_encoddings_choices)
	for idx in range(config.plugins.e2jellyfinclient.connectioncount.value):
		initConnection(idx)


def getActiveConnection():
	try:
		name = config.plugins.e2jellyfinclient.connections[config.plugins.e2jellyfinclient.activeconnection.value].name.value
		url = config.plugins.e2jellyfinclient.connections[config.plugins.e2jellyfinclient.activeconnection.value].ip.value
		port = config.plugins.e2jellyfinclient.connections[config.plugins.e2jellyfinclient.activeconnection.value].port.value
		username = config.plugins.e2jellyfinclient.connections[config.plugins.e2jellyfinclient.activeconnection.value].user.value
		password = config.plugins.e2jellyfinclient.connections[config.plugins.e2jellyfinclient.activeconnection.value].password.value
		return (name, url, port, username, password)
	except:
		return ("", "", 0, "", "")


class EmbySetup(Setup):
	def __init__(self, session, args=None):
		self.connections = []
		self.connectionItems = []
		self.createItems()
		Setup.__init__(self, session, "e2jellyfinclient", plugin="Extensions/E2JellyfinClient", PluginLanguageDomain=PluginLanguageDomain)
		self["key_yellow"] = StaticText(_("Add"))
		self["key_blue"] = StaticText(_("Remove"))
		self["selectEntriesActions"] = HelpableActionMap(self, ["ColorActions"],
		{
			"yellow": (self.keyYellow, _("Add Connection")),
			"blue": (self.keyBlue, _("Remove Connection"))
		}, prio=0, description=_("Setup Actions"))

	def updateButtons(self):
		current = self["config"].getCurrent()
		if current:
			if len(current) > 3:
				self["key_yellow"].setText(_("Edit"))
				self["key_blue"].setText(_("Remove"))
			else:
				self["key_yellow"].setText(_("Add"))
				self["key_blue"].setText("")
			self["selectEntriesActions"].setEnabled(True)
		else:
			self["selectEntriesActions"].setEnabled(False)

	def createItems(self):
		self.connectionItems = []
		for index in range(config.plugins.e2jellyfinclient.connectioncount.value):
			item = config.plugins.e2jellyfinclient.connections[index]
			self.connectionItems.append((f"{item.name.value}", ConfigYesNo(default=config.plugins.e2jellyfinclient.activeconnection.value == index), "", index, item))

	def createSetup(self):  # NOSONAR silence S2638
		Setup.createSetup(self)
		self.list = self.list + self.connectionItems
		currentItem = self["config"].getCurrent()
		self["config"].setList(self.list)
		self.moveToItem(currentItem)

	def selectionChanged(self):
		self.updateButtons()
		Setup.selectionChanged(self)

	def calculateActive(self, index, active):
		config.plugins.e2jellyfinclient.activeconnection.value = index if active else 0
		config.plugins.e2jellyfinclient.activeconnection.save()
		config.plugins.e2jellyfinclient.save()
		self.createItems()
		self.createSetup()

	def changedEntry(self):
		current = self["config"].getCurrent()
		if current and len(current) == 5:
			self.calculateActive(current[3], current[1].value)
			return
		Setup.changedEntry(self)

	def keyBlue(self):
		current = self["config"].getCurrent()
		if current and len(current) == 5:  # Remove
			config.plugins.e2jellyfinclient.connections.remove(current[4])
			config.plugins.e2jellyfinclient.connections.save()
			config.plugins.e2jellyfinclient.connectioncount.value = len(config.plugins.e2jellyfinclient.connections)
			config.plugins.e2jellyfinclient.connectioncount.save()
			self.calculateActive(0, True)

	def keyYellow(self):
		def connectionCallback(index, result=None):
			if result:
				config.plugins.e2jellyfinclient.connections[index] = result
				config.plugins.e2jellyfinclient.connections.save()
				config.plugins.e2jellyfinclient.connectioncount.value = index + 1
				config.plugins.e2jellyfinclient.connectioncount.save()
				self.calculateActive(index, True)

		current = self["config"].getCurrent()
		if current and len(current) == 5:  # Edit
			currentItem = current[4]
			index = config.plugins.e2jellyfinclient.connections.index(currentItem)
		else:  # Add
			index = len(config.plugins.e2jellyfinclient.connections)
			currentItem = initConnection(index)
		self.session.openWithCallback(boundFunction(connectionCallback, index), EmbyConnections, currentItem)


class EmbyConnections(Setup):
	def __init__(self, session, entry):
		self.entry = entry
		Setup.__init__(self, session, "e2embyclientconnection", plugin="Extensions/E2JellyfinClient", PluginLanguageDomain=PluginLanguageDomain)

	def keySave(self):
		Setup.saveAll(self)
		self.close(self.entry)
