#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
"""
#########################################################
#                                                       #
#  Advanced Screenshot                                  #
#  Version: 1.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#                                                       #
#  Last Modified: "11:37 - 20250515"                    #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#                                                       #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""
__author__ = "Lululla"

# Standard Library Imports
import subprocess
import time
from datetime import datetime
from os import (
    access, chmod, listdir, makedirs, remove, stat, W_OK, X_OK
)
from os.path import exists, getctime, isdir, isfile, join  # , getsize
from re import match

# Third-party Imports
try:
    from Components.AVSwitch import AVSwitch
except ImportError:
    from Components.AVSwitch import eAVControl as AVSwitch
from enigma import eActionMap, ePicLoad, getDesktop
from twisted.web import resource, server

# Application-specific Imports
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import (
    ConfigEnableDisable, ConfigInteger, ConfigSelection, ConfigSubsection,
    ConfigYesNo, config, getConfigListEntry, ConfigNothing, NoSave
)
from Components.Label import Label
from Components.Harddisk import harddiskmanager
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import resolveFilename, SCOPE_MEDIA

# Local specific Imports
from . import _, __version__
from .MyConsole import MyConsole

# Constants
SIZE_W = getDesktop(0).size().width()
SIZE_H = getDesktop(0).size().height()


def get_scale():
    """Get framebuffer scale."""
    return AVSwitch().getFramebufferScale()


BUTTON_MAP = {
    "059": "KEY_F1",
    "060": "KEY_F2",
    "061": "KEY_F3",
    "062": "KEY_F4",
    "063": "KEY_F5",
    "064": "KEY_F6",
    "065": "KEY_F7",
    "066": "KEY_F8",
    "067": "KEY_F9",
    "068": "KEY_F10",
    "102": "KEY_HOME",
    "113": "Mute",
    "167": "KEY_RECORD",
    "138": "Help",
    "358": "Info",
    "362": "Timer",
    "365": "EPG",
    "370": "Subtitle",
    "377": "TV",
    "385": "Radio",
    "388": "Text",
    "392": "Audio",
    "398": "Red",
    "399": "Green",
    "400": "Yellow",
    "401": "Blue"
}


MODE_MAP = {
    "osd": "-o",
    "video": "-v",
    "All": ""
}


def get_mounted_devices():
    """Get list of mounted devices that are writable.

    Returns:
        List of tuples (mount_point, description)
    """
    def handle_mountpoint(location):
        """Normalize mountpoint and create description."""
        original_mp, original_desc = location
        normalized_mp = original_mp.rstrip('/') + '/'
        if original_desc:
            new_desc = original_desc + " (" + normalized_mp + ")"
        else:
            new_desc = "(" + normalized_mp + ")"
        return (normalized_mp, new_desc)

    # Start with standard media locations
    mounted_devices = [
        (resolveFilename(SCOPE_MEDIA, 'hdd'), _('Hard Disk')),
        (resolveFilename(SCOPE_MEDIA, 'usb'), _('USB Drive'))
    ]

    # Add mounted partitions
    mounted_devices += [
        (partition.mountpoint, _(partition.description) if partition.description else '')
        for partition in harddiskmanager.getMountedPartitions(True)
    ]

    # Filter only writable directories
    mounted_devices = [
        path for path in mounted_devices
        if isdir(path[0]) and access(path[0], W_OK | X_OK)
    ]

    # Add network mounts
    net_dir = resolveFilename(SCOPE_MEDIA, 'net')
    if isdir(net_dir):
        mounted_devices += [
            (join(net_dir, path), _('Network mount'))
            for path in listdir(net_dir)
        ]

    # Add temporary directory
    mounted_devices += [(join('/', 'tmp'), _('Temporary'))]

    # Normalize all mountpoints
    mounted_devices = list(map(handle_mountpoint, mounted_devices))

    return mounted_devices


# Configuration
config.plugins.AdvancedScreenshot = ConfigSubsection()
config.plugins.AdvancedScreenshot.enabled = ConfigEnableDisable(default=True)
config.plugins.AdvancedScreenshot.freezeframe = ConfigEnableDisable(
    default=False)
config.plugins.AdvancedScreenshot.allways_save = ConfigEnableDisable(
    default=False)
config.plugins.AdvancedScreenshot.fixed_aspect_ratio = ConfigEnableDisable(
    default=False)
config.plugins.AdvancedScreenshot.always_43 = ConfigEnableDisable(
    default=False)
config.plugins.AdvancedScreenshot.bi_cubic = ConfigEnableDisable(default=False)

config.plugins.AdvancedScreenshot.picturesize = ConfigSelection(
    default="1920x1080",
    choices=[
        ("1920x1080", "1080p (Full HD)"),
        ("1280x720", "720p (HD)"),
        ("720x576", "576p (SD)"),
        ("default", _("Default Resolution"))
    ]
)

config.plugins.AdvancedScreenshot.pictureformat = ConfigSelection(
    default="-j 90",
    choices=[
        ('-j 100', _('JPEG 100%')),
        ('-j 90', _('JPEG 90%')),
        ('-j 80', _('JPEG 80%')),
        ('-j 60', _('JPEG 60%')),
        ('-p', _('PNG')),
        ('bmp', _('BMP'))
    ]
)

config.plugins.AdvancedScreenshot.path = ConfigSelection(
    default="/tmp/",
    choices=get_mounted_devices()
)

config.plugins.AdvancedScreenshot.picturetype = ConfigSelection(
    default="video",
    choices=[
        ("osd", _("OSD Only")),
        ("video", _("Video Only")),
        ("All", _("OSD + Video"))
    ]
)

config.plugins.AdvancedScreenshot.timeout = ConfigSelection(
    default="3",
    choices=[
        ("1", "1 sec"),
        ("3", "3 sec"),
        ("5", "5 sec"),
        ("10", "10 sec"),
        ("off", _("no message")),
        ("0", _("no timeout"))
    ]
)

config.plugins.AdvancedScreenshot.buttonchoice = ConfigSelection(
    default="138",
    choices=BUTTON_MAP
)

config.plugins.AdvancedScreenshot.switchhelp = ConfigYesNo(default=False)
config.plugins.AdvancedScreenshot.capture_delay = ConfigInteger(
    default=0, limits=(0, 10))

# Dummy for padding/compatibility
config.plugins.AdvancedScreenshot.dummy = ConfigSelection(
    default="1",
    choices=[("1", " ")]
)


def cleanup_tmp_files(tmp_folder="/tmp", max_age_seconds=3600):
    """Clean up temporary screenshot files.

    Args:
        tmp_folder: Temporary folder path
        max_age_seconds: Maximum age for files to keep
    """
    now = time.time()
    for filename in listdir(tmp_folder):
        if filename.startswith("web_grab_") and (
                filename.endswith(".png") or filename.endswith(".jpg")):
            filepath = tmp_folder + "/" + filename
            try:
                file_stat = stat(filepath)
                if now - file_stat.st_mtime > max_age_seconds:
                    remove(filepath)
            except Exception:
                pass


def check_folder(folder):
    """Check if folder exists, create if it doesn't.

    Args:
        folder: Folder path to check

    Returns:
        True if folder exists or was created successfully
    """
    if exists(folder):
        return True
    else:
        makedirs(folder, exist_ok=True)
        return True


def get_extension(fmt):
    """Map format string to file extension.

    Args:
        fmt: Format string (e.g., '-j 90', '-p', 'bmp')

    Returns:
        File extension with dot (e.g., '.jpg', '.png', '.bmp')
    """
    if fmt.startswith('-j'):
        return '.jpg'
    elif fmt == '-p':
        return '.png'
    elif fmt == 'bmp':
        return '.bmp'
    return '.jpg'  # fallback


def generate_filename():
    """Generate unique filename for screenshot.

    Returns:
        Full path to screenshot file or None on error
    """
    base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
    full_path = base_path + "/screenshots"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pic_format = config.plugins.AdvancedScreenshot.pictureformat.value
    extension = get_extension(pic_format)

    try:
        makedirs(full_path, exist_ok=True)
        for path in [base_path, full_path]:
            if not exists(path):
                raise Exception("Folder " + path + " does not exist")
            if not access(path, W_OK):
                raise Exception("Write permission denied for " + path)
        chmod(full_path, 0o777)
    except Exception as e:
        print("[ERROR] Creating directory: " + str(e))
        return None

    return full_path + "/screenshot_" + timestamp + extension


def build_grab_command(filename):
    """Build grab command for screenshot capture.

    Args:
        filename: Output filename

    Returns:
        List of command arguments
    """
    cmd = ["/usr/bin/grab"]

    # Add -d parameter if not using dpkg
    if not exists('/var/lib/dpkg/status'):
        cmd += ["-d"]

    # Add picture type parameter
    pic_type = config.plugins.AdvancedScreenshot.picturetype.value
    if pic_type in MODE_MAP and MODE_MAP[pic_type]:
        cmd.append(MODE_MAP[pic_type])

    # Add aspect ratio fix
    if config.plugins.AdvancedScreenshot.fixed_aspect_ratio.value:
        cmd.append("-n")

    # Add 4:3 forcing
    if config.plugins.AdvancedScreenshot.always_43.value:
        cmd.append("-l")

    # Add bicubic resize
    if config.plugins.AdvancedScreenshot.bi_cubic.value:
        cmd.append("-b")

    # Add format parameter
    pic_format = config.plugins.AdvancedScreenshot.pictureformat.value
    if pic_format.startswith('-j'):
        cmd += pic_format.split()  # Example: "-j 90" → ["-j", "90"]
    elif pic_format == '-p':
        cmd.append("-p")

    # Add output filename
    cmd.append(filename)

    return cmd


class WebGrabResource(resource.Resource):
    """Web interface handler for remote screenshot capture."""

    def __init__(self, session):
        """Initialize web resource.

        Args:
            session: Session object
        """
        resource.Resource.__init__(self)
        self.session = session

    def render_GET(self, request):
        """Handle GET requests for screenshot capture.

        Args:
            request: HTTP request object

        Returns:
            server.NOT_DONE_YET
        """
        try:
            cleanup_tmp_files()

            # Parse parameters
            format_param = request.args.get(b'format', [b'-j 90'])[0].decode()
            resolution = request.args.get(b'r', [b'720'])[0].decode()
            # video_param = request.args.get(b'v', [b'0'])[0].decode()
            save_param = request.args.get(b's', [b'1'])[0].decode()

            # Validate format
            valid_formats = ('-j 100', '-j 90', '-j 80', '-j 60', 'bmp', '-p')
            if format_param not in valid_formats:
                raise ValueError("[AdvancedScreenshot] Format not supported")

            # Validate resolution
            if resolution != 'default' and not match(
                    r"^\d+(x\d+)?$", resolution):
                raise ValueError("[AdvancedScreenshot] Invalid resolution")

            # Generate filename
            filename = generate_filename()

            # Build and execute command
            cmd = build_grab_command(filename)
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if not exists(filename):
                if result.returncode == 0:
                    # Set dynamic Content-Type
                    ext = get_extension(format_param)
                    with open(filename, 'rb') as f:
                        request.setHeader(b'Content-Type', 'image/' + ext)
                        request.write(f.read())
                    # Clean up if requested
                    if int(save_param) == 1 and exists(filename):
                        remove(filename)
                else:
                    request.setResponseCode(500)
                    request.write("Error: " + result.stderr.decode())
            else:
                request.setResponseCode(500)
                request.write("Error: File not created")

        except Exception as e:
            request.setResponseCode(500)
            request.write("[AdvancedScreenshot] Error: " + str(e))

        return server.NOT_DONE_YET


class ScreenshotCore:
    """Core screenshot functionality with hotkey support."""

    def __init__(self, session):
        """Initialize screenshot core.

        Args:
            session: Session object
        """
        self.session = session
        self.previous_flag = 0
        self.myConsole = MyConsole()
        self._bind_hotkey()

    def _bind_hotkey(self):
        """Bind hotkey for screenshot capture."""
        eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self._key_handler)

    def _key_handler(self, key, flag):
        """Handle key press events.

        Args:
            key: Key code
            flag: Key press flag

        Returns:
            0 to pass event, 1 to consume event
        """
        try:
            current_value = str(key)
            target_value = config.plugins.AdvancedScreenshot.buttonchoice.value

            # If button is NOT configured for screenshot, let it pass
            if current_value != target_value:
                return 0

            # If it is the screenshot button and plugin is enabled
            if config.plugins.AdvancedScreenshot.enabled.value:
                if config.plugins.AdvancedScreenshot.switchhelp.value:
                    # Short press mode
                    if flag == 1:
                        self.capture()
                        return 1
                else:
                    # Long press mode
                    if flag == 3:
                        self.capture()
                        return 1

            return 0
        except Exception as e:
            print("[AdvancedScreenshot] Key handler error: " + str(e))
            return 0

    def capture(self):
        """Capture screenshot."""
        if not self._is_grab_available():
            self._show_error(_("Web capture failed: Grab not available"))
            return

        try:
            filename = generate_filename()
            if not filename:
                return
            cmd = build_grab_command(filename)
            self.last_capture_filename = filename
            print("[Capture] Running command: " + " ".join(cmd))
            self.myConsole.ePopen(cmd, self._capture_callback, [filename])
        except Exception as e:
            print("[AdvancedScreenshot][ERROR] Capture error: " + str(e))
            self._show_error(_("Error during capture:\n") + str(e))

    def _capture_callback(self, data, retval, extra_args):
        """Callback for capture completion.

        Args:
            data: Command output data
            retval: Return value
            extra_args: Extra arguments (filename)
        """
        print(
            "[AdvancedScreenshot][_capture_callback] extra_args: " +
            str(extra_args))
        filename = extra_args
        error_msg = ""

        if retval != 0:
            error_msg = "Grab command failed with code: " + str(retval)

        if not error_msg and filename:
            # Wait for file creation with retries
            for x in range(5):
                if exists(filename):
                    break
                time.sleep(0.5)
            else:
                error_msg = "File not created\nCheck disk space"

        if error_msg:
            print("[AdvancedScreenshot][ERROR]: " + str(error_msg))
            self._show_error(_(error_msg))
            return

        print("[AdvancedScreenshot][INFO] Screenshot saved: " + str(filename))
        if config.plugins.AdvancedScreenshot.freezeframe.value:
            self.session.openWithCallback(
                self._freeze_callback, FreezeFrame, filename)
        else:
            self._show_message(_("Screenshot saved successfully!"))

    def _freeze_callback(self, retval):
        """Callback for freeze frame preview.

        Args:
            retval: Return value from freeze frame
        """
        if retval:
            self._show_message(_("Screenshot saved successfully!"))

    def _is_grab_available(self):
        """Check if grab utility is available.

        Returns:
            True if /usr/bin/grab exists
        """
        return exists("/usr/bin/grab")

    def _show_message(self, message):
        """Show success notification.

        Args:
            message: Message to display
        """
        timeout_str = config.plugins.AdvancedScreenshot.timeout.value
        if timeout_str == "off" or timeout_str == "0":
            timeout = None
        else:
            timeout = int(timeout_str)

        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_INFO,
            timeout=timeout
        )

    def _show_error(self, message):
        """Show error notification.

        Args:
            message: Error message to display
        """
        self.session.open(
            MessageBox,
            message,
            MessageBox.TYPE_ERROR,
            timeout=5
        )


class FreezeFrame(Screen):
    """Screen for freeze frame preview of captured screenshot."""

    skin = """
    <screen name="FreezeFrame" position="0,0" size="""" + str(SIZE_W) + ", " + str(SIZE_H) + """" flags="wfNoBorder">
        <widget name="preview" position="0,0" size="""" + str(SIZE_W) + ", " + str(SIZE_H) + """" zPosition="4" />
        <widget name="info" position="center,50" size="600,40" font="Regular;28" zPosition="5" halign="center"/>
    </screen>"""

    def __init__(self, session, filename):
        """Initialize freeze frame screen.

        Args:
            session: Session object
            filename: Path to screenshot file
        """
        Screen.__init__(self, session)
        self.filename = filename
        self.picload = ePicLoad()
        self.scale = get_scale()
        self["preview"] = Pixmap()
        self["info"] = Label(_("Press OK to save - EXIT to cancel"))
        self["actions"] = ActionMap(["OkCancelActions"], {
            "ok": self.save,
            "cancel": self.discard
        })
        try:
            self.picload.PictureData.get().append(self.decode_picture)
        except BaseException:
            self.picload_conn = self.picload.PictureData.connect(
                self.decode_picture)
        print("[FreezeFrame] File " + self.filename)
        self.onLayoutFinish.append(self.show_picture)

    def show_picture(self):
        """Load and display picture."""
        if exists(self.filename):
            print("[FreezeFrame] show_picture: " + str(self.filename))

        scalex = self.scale[0] if isinstance(
            self.scale[0], (int, float)) else 1
        scaley = self.scale[1] if isinstance(
            self.scale[1], (int, float)) else 1

        self.picload.setPara([
            self["preview"].instance.size().width(),
            self["preview"].instance.size().height(),
            scalex,
            scaley,
            0,
            1,
            "#ff000000"
        ])

        if self.picload.startDecode(self.filename):
            self.picload = ePicLoad()
            try:
                self.picload.PictureData.get().append(self.decode_picture)
            except BaseException:
                self.picload_conn = self.picload.PictureData.connect(
                    self.decode_picture)

    def decode_picture(self, pic_info=None):
        """Decode and display picture.

        Args:
            pic_info: Picture information
        """
        print("[FreezeFrame] decode_picture: " + str(pic_info))
        ptr = self.picload.getData()
        if ptr is not None:
            self["preview"].instance.setPixmap(ptr)
            self["preview"].instance.show()

    def save(self):
        """Save screenshot."""
        self.close(True)

    def discard(self):
        """Discard screenshot."""
        self.close(False)


class ScreenshotGallery(Screen):
    """Screen for browsing captured screenshots."""

    skin = """
    <screen position="center,center" size="1280,720" title="Screenshot Gallery" flags="wfNoBorder">
        <widget name="list" position="40,40" size="620,560" itemHeight="35" font="Regular;32" />
        <eLabel position="345,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#0000ff00" text="OK" halign="center" />
        <eLabel position="643,670" size="300,40" font="Regular;36" backgroundColor="#00ffa000" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Delete" halign="center" />
        <widget name="preview" position="682,126" size="550,350" zPosition="9" alphatest="blend" scale="1" />
        <widget name="info" position="44,606" zPosition="4" size="1189,55" font="Regular;28" foregroundColor="yellow" transparent="1" halign="center" valign="center" />
        <eLabel backgroundColor="#00ff0000" position="45,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="345,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#00ffff00" position="643,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#000000ff" position="944,710" size="300,6" zPosition="12" />
    </screen>"""

    def __init__(self, session):
        """Initialize screenshot gallery.

        Args:
            session: Session object
        """
        Screen.__init__(self, session)
        self.screenshots = []
        self['list'] = MenuList(self.screenshots)
        self['preview'] = Pixmap()

        base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
        self.full_path = base_path + "/screenshots"

        if not self.full_path.endswith("/"):
            self.full_path += "/"

        if check_folder(self.full_path):
            print('[ScreenshotGallery] Folder exists')

        self.scale = get_scale()
        self.picload = ePicLoad()
        try:
            self.picload.PictureData.get().append(self.decode_picture)
        except BaseException:
            self.picload_conn = self.picload.PictureData.connect(
                self.decode_picture)

        self['info'] = Label()
        self["list"].onSelectionChanged.append(self.show_picture)
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
            "red": self.close,
            "green": self.preview,
            "yellow": self.delete,
            "up": self.key_up,
            "down": self.key_down,
            "left": self.key_left,
            "right": self.key_right,
            "ok": self.preview,
            "cancel": self.close,
        })
        self._load_screenshots()
        self.onLayoutFinish.append(self.show_picture)

    def _load_screenshots(self):
        """Load screenshot list from directory."""
        print("[ScreenshotGallery] Path: " + str(self.full_path))
        try:
            image_extensions = (".jpg", ".png", ".bmp", ".JPG", ".PNG", ".BMP")
            self.screenshots = sorted([
                f for f in listdir(self.full_path)
                if f.endswith(image_extensions)
            ], key=lambda x: getctime(join(self.full_path, x)), reverse=True)
            print("[ScreenshotGallery] Found " +
                  str(len(self.screenshots)) + " screenshots")
            self["list"].setList(self.screenshots)
        except Exception as e:
            self.session.open(
                MessageBox,
                _("Error loading gallery: ") +
                str(e),
                MessageBox.TYPE_ERROR)

    def show_picture(self):
        """Show selected picture in preview."""
        fname = self['list'].getCurrent()
        if not fname:
            return

        self.filename = self.full_path + str(fname)
        print('[ScreenshotGallery] show_picture: ' + self.filename)

        scalex = self.scale[0] if isinstance(
            self.scale[0], (int, float)) else 1
        scaley = self.scale[1] if isinstance(
            self.scale[1], (int, float)) else 1

        self.picload.setPara([
            self["preview"].instance.size().width(),
            self["preview"].instance.size().height(),
            scalex,
            scaley,
            0,
            1,
            "#ff000000"
        ])

        if self.picload.startDecode(self.filename):
            self.picload = ePicLoad()
            try:
                self.picload.PictureData.get().append(self.decode_picture)
            except BaseException:
                self.picload_conn = self.picload.PictureData.connect(
                    self.decode_picture)

    def decode_picture(self, pic_info=""):
        """Decode and display picture.

        Args:
            pic_info: Picture information
        """
        if len(self.screenshots) > 0:
            print("[ScreenshotGallery] decode_picture: " + str(pic_info))
            if self.filename is not None:
                ptr = self.picload.getData()
            else:
                fname = self['list'].getCurrent()
                self.filename = self.full_path + str(fname)
                ptr = self.picload.getData()

            print("[ScreenshotGallery] decode_picture filename: " +
                  str(self.filename))
            self["info"].setText(_(self.filename))
            if ptr:
                self["preview"].instance.setPixmap(ptr)
                self["preview"].instance.show()

    def key_up(self):
        """Handle up key press."""
        print("[DEBUG] up pressed")
        try:
            self['list'].up()
            self.show_picture()
        except Exception as e:
            print(e)

    def key_down(self):
        """Handle down key press."""
        print("[DEBUG] down pressed")
        try:
            self['list'].down()
            self.show_picture()
        except Exception as e:
            print(e)

    def key_left(self):
        """Handle left key press."""
        try:
            self['list'].pageUp()
            self.show_picture()
        except Exception as e:
            print(e)

    def key_right(self):
        """Handle right key press."""
        try:
            self['list'].pageDown()
            self.show_picture()
        except Exception as e:
            print(e)

    def preview(self):
        """Open full screen preview of selected screenshot."""
        selection = self["list"].getCurrent()
        if selection:
            path = join(self.full_path, selection)
            self.session.open(ScreenshotPreview, path)

    def delete(self, confirm=False):
        """Delete selected screenshot.

        Args:
            confirm: Whether confirmation was already given
        """
        if not confirm:
            self.session.openWithCallback(
                self.delete, MessageBox,
                _("Are you sure you want to delete this screenshot?"),
                MessageBox.TYPE_YESNO
            )
        else:
            selection = self["list"].getCurrent()
            if selection:
                try:
                    remove(join(self.full_path, selection))
                    self._load_screenshots()
                except Exception as e:
                    self.session.open(
                        MessageBox,
                        _("Delete failed: ") + str(e),
                        MessageBox.TYPE_ERROR)


class ScreenshotPreview(Screen):
    """Full screen preview of screenshot."""

    skin = """
    <screen position="0,0" size="""" + str(SIZE_W) + ", " + str(SIZE_H) + """" title="Screenshot Preview" flags="wfNoBorder">
        <widget name="image" position="0,0" size="""" + str(SIZE_W) + ", " + str(SIZE_H) + """" />
    </screen>"""

    def __init__(self, session, filepath):
        """Initialize screenshot preview.

        Args:
            session: Session object
            filepath: Path to screenshot file
        """
        Screen.__init__(self, session)
        self.filepath = filepath
        self["image"] = Pixmap()
        self["actions"] = ActionMap(
            ["OkCancelActions"], {
                "cancel": self.close})
        self._show_image()

    def _show_image(self):
        """Load and display image."""
        self.picload = ePicLoad()
        try:
            self.picload.PictureData.get().append(self._update_image)
        except BaseException:
            self.picload_conn = self.picload.PictureData.connect(
                self._update_image)

        self.picload.setPara((
            SIZE_W, SIZE_H,
            SIZE_W, SIZE_H,
            False, 1, "#00000000"
        ))
        self.picload.startDecode(self.filepath)

    def _update_image(self, pic_info=None):
        """Update displayed image.

        Args:
            pic_info: Picture information
        """
        ptr = self.picload.getData()
        if ptr:
            self["image"].instance.setPixmap(ptr)


class AdvancedScreenshotConfig(ConfigListScreen, Screen):
    """Configuration screen for Advanced Screenshot plugin."""

    skin = """
    <screen name="AdvancedScreenshotConfig" position="center,center" size="1280,720" title="Screenshot Settings" flags="wfNoBorder">
        <widget name="config" position="50,50" size="1180,600" scrollbarMode="showNever" itemHeight="35" font="Regular;32" />
        <eLabel position="45,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#0000ff00" text="OK" halign="center" />
        <eLabel position="345,670" size="300,40" font="Regular;36" backgroundColor="#b3ffd9" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Cancel" halign="center" />
        <eLabel position="643,670" size="300,40" font="Regular;36" backgroundColor="#00ffa000" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="Galery" halign="center" />
        <eLabel position="944,670" size="300,40" font="Regular;36" backgroundColor="#3e91f6" foregroundColor="#000000" borderWidth="1" zPosition="4" borderColor="#00ffa000" text="List" halign="center" />
        <eLabel backgroundColor="#00ff0000" position="45,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#0000ff00" position="345,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#00ffff00" position="643,710" size="300,6" zPosition="12" />
        <eLabel backgroundColor="#000000ff" position="944,710" size="300,6" zPosition="12" />
    </screen>"""

    def __init__(self, session):
        """Initialize configuration screen.

        Args:
            session: Session object
        """
        Screen.__init__(self, session)
        self.setup_title = _("Settings")
        self.list = []
        self._on_config_entry_changed = []
        self["config"] = ConfigList(self.list)
        self._create_config()
        ConfigListScreen.__init__(
            self,
            self.list,
            session=self.session,
            on_change=self._on_config_entry_changed)

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions", "VirtualKeyboardActions"],
            {
                "ok": self.save,
                "cancel": self.cancel,
                "blue": self.on_gallery,
                "yellow": self.on_pic_view,
                "green": self.save,
                "red": self.cancel,
                "showVirtualKeyboard": self.key_text,
            }
        )
        self.onLayoutFinish.append(self.__layout_finished)

    def __layout_finished(self):
        """Called when layout is finished."""
        self.setTitle(self.setup_title)

    def _create_config(self):
        """Create configuration list."""
        self.list = []

        # Header
        section = '--------------------------------------( Advanced Screenshot Setup )--------------------------------------'
        self.list.append((_(section), NoSave(ConfigNothing())))
        self.list.append(
            getConfigListEntry(
                _("Enable plugin"),
                config.plugins.AdvancedScreenshot.enabled))

        if config.plugins.AdvancedScreenshot.enabled.value:
            # Image format
            self.list.append(getConfigListEntry(
                _("Image format"),
                config.plugins.AdvancedScreenshot.pictureformat
            ))

            # Resolution
            self.list.append(getConfigListEntry(
                _("Resolution"),
                config.plugins.AdvancedScreenshot.picturesize
            ))

            # Aspect ratio fix
            self.list.append(getConfigListEntry(
                _("Fix aspect ratio (adds -n to force no stretching)"),
                config.plugins.AdvancedScreenshot.fixed_aspect_ratio
            ))

            # Force 4:3 output
            self.list.append(
                getConfigListEntry(
                    _("Always output 4:3 image (adds letterbox if source is 16:9)"),
                    config.plugins.AdvancedScreenshot.always_43))

            # Bicubic resize
            self.list.append(getConfigListEntry(
                _("Use bicubic resize (slower, but smoother image)"),
                config.plugins.AdvancedScreenshot.bi_cubic
            ))

            # Freeze frame preview
            self.list.append(getConfigListEntry(
                _("Freeze frame preview"),
                config.plugins.AdvancedScreenshot.freezeframe
            ))

            if config.plugins.AdvancedScreenshot.freezeframe.value:
                self.list.append(getConfigListEntry(
                    _("Always save screenshots"),
                    config.plugins.AdvancedScreenshot.allways_save
                ))

            # Save path
            self.list.append(getConfigListEntry(
                _("Save path (requires restart)"),
                config.plugins.AdvancedScreenshot.path
            ))

            # Key mapping
            self.list.append(getConfigListEntry(
                _("Select screenshot button"),
                config.plugins.AdvancedScreenshot.buttonchoice
            ))

            current_value = config.plugins.AdvancedScreenshot.buttonchoice.value
            button_name = BUTTON_MAP.get(current_value, _("Unknown"))

            if current_value in ("398", "399", "400"):
                self.list.append(
                    getConfigListEntry(
                        _("Long press required for ") +
                        button_name +
                        _(" long ' can be used."),
                        config.plugins.AdvancedScreenshot.dummy))
                config.plugins.AdvancedScreenshot.switchhelp.setValue(0)
            else:
                self.list.append(
                    getConfigListEntry(
                        _("Press type for ") +
                        button_name +
                        _(" ' button instead of ' ") +
                        button_name +
                        _(" long:"),
                        config.plugins.AdvancedScreenshot.switchhelp))

            # Timeout
            self.list.append(getConfigListEntry(
                _("Message timeout (seconds)"),
                config.plugins.AdvancedScreenshot.timeout
            ))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def _on_config_entry_changed(self, config_element=None):
        """Handle configuration entry changes.

        Args:
            config_element: Changed configuration element
        """
        for x in self.onChangedEntry:
            x()
        self._create_config()

    def save(self):
        """Save configuration."""
        base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
        full_path = base_path + "/screenshots/"
        if check_folder(full_path):
            print(full_path)

        for x in self["config"].list:
            if isinstance(x, tuple) and len(x) > 1 and hasattr(x[1], "save"):
                x[1].save()
        self.close(True)

    def cancel(self):
        """Cancel configuration changes."""
        self.close(False)

    def key_text(self):
        """Open virtual keyboard for text input."""
        sel = self["config"].getCurrent()
        if sel:
            text_value = str(sel[1].value)
            self.session.openWithCallback(
                self.virtual_keyboard_callback,
                VirtualKeyBoard,
                title=sel[0],
                text=text_value
            )

    def virtual_keyboard_callback(self, callback=None):
        """Handle virtual keyboard callback.

        Args:
            callback: Text from virtual keyboard
        """
        if callback is not None:
            current = self["config"].getCurrent()
            cfg = current[1]
            try:
                if hasattr(cfg, "base"):
                    cfg.value = int(callback)
                else:
                    cfg.value = callback
            except Exception:
                pass
            self["config"].invalidate(current)

    def get_current_entry(self):
        """Get current configuration entry name.

        Returns:
            Current entry name
        """
        current = self["config"].getCurrent()
        if current:
            return current[0]
        return ""

    def get_current_value(self):
        """Get current configuration value.

        Returns:
            Current value as string
        """
        current = self["config"].getCurrent()
        if current and hasattr(current[1], "getText"):
            return str(current[1].getText())
        return str(current[1]) if current else ""

    def create_summary(self):
        """Create summary for setup screen.

        Returns:
            SetupSummary instance
        """
        from Screens.Setup import SetupSummary
        return SetupSummary

    def key_left(self):
        """Handle left key press."""
        ConfigListScreen.keyLeft(self)
        self._create_config()

    def key_right(self):
        """Handle right key press."""
        ConfigListScreen.keyRight(self)
        self._create_config()

    def key_down(self):
        """Handle down key press."""
        self['config'].instance.moveSelection(self['config'].instance.moveDown)
        self._create_config()

    def key_up(self):
        """Handle up key press."""
        self['config'].instance.moveSelection(self['config'].instance.moveUp)
        self._create_config()

    def on_pic_view(self):
        """Open picture view gallery."""
        fullpath = []
        base_path = config.plugins.AdvancedScreenshot.path.value.rstrip('/')
        full_path = base_path + "/screenshots/"
        print(
            "[AdvancedScreenshotConfig] on_pic_view full_path: " +
            str(full_path))

        if check_folder(full_path):
            for filename in listdir(full_path):
                if isfile(full_path + filename):
                    print(
                        "[AdvancedScreenshotConfig] on_pic_view file: " +
                        str(filename))
                    if filename.lower().endswith(('.jpg', '.png', '.bmp', '.gif')):
                        fullpath.append(filename)
            self.fullpath = fullpath
            try:
                from .picplayer import Galery_Thumb
                self.session.open(Galery_Thumb, self.fullpath, 0, full_path)
            except (TypeError, ImportError) as e:
                print("[AdvancedScreenshotConfig] on_pic_view error: " + str(e))

    def on_gallery(self):
        """Open screenshot gallery."""
        try:
            self.session.open(ScreenshotGallery)
        except Exception as e:
            print("[AdvancedScreenshotConfig] on_gallery error: " + str(e))


def get_button_name(value):
    """Get button name from value.

    Args:
        value: Button value

    Returns:
        Button name or "Unknown"
    """
    return BUTTON_MAP.get(value, _("Unknown"))


def get_available_buttons():
    """Get list of available button codes.

    Returns:
        List of button codes
    """
    return list(BUTTON_MAP.keys())


def session_start(reason, session=None, **kwargs):
    """Initialize plugin components on session start.

    Args:
        reason: Reason code
        session: Session object
        **kwargs: Additional arguments

    Returns:
        ScreenshotCore instance or None
    """
    print("[AdvancedScreenshot] session_start: " +
          str(reason) + " session " + str(session))

    if reason == 0 and session:
        # Register web interface
        root = kwargs.get('root', None)
        if root:
            root.putChild(b'grab', WebGrabResource(session))
        print("[AdvancedScreenshot] session_start root: " + str(root))
        return ScreenshotCore(session)

    return None


def setup(session, **kwargs):
    """Open setup screen.

    Args:
        session: Session object
        **kwargs: Additional arguments
    """
    session.open(AdvancedScreenshotConfig)


def plugins(**kwargs):
    """Get plugin descriptors.

    Args:
        **kwargs: Additional arguments

    Returns:
        List of PluginDescriptor objects
    """
    return [
        PluginDescriptor(
            where=PluginDescriptor.WHERE_SESSIONSTART,
            fnc=session_start),
        PluginDescriptor(
            name=_("Advanced Screenshot"),
            description=_("Professional screenshot tool") +
            " " +
            __version__,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=setup),
        PluginDescriptor(
            name=_("Advanced Screenshot Gallery"),
            description=_("View captured screenshots"),
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=lambda session: session.open(ScreenshotGallery))]
