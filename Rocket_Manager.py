from xml.etree import ElementTree
import sys
import time
import os
import urllib
import zipfile
import shutil
import socket
import platform


# --Constants

MANAGER_FOLDER = "_RocketManager\\"

ROCKET_EXTRACT_FOLDER = MANAGER_FOLDER + "last_rocket_download"
BACKUP_BUNDLES_FOLDER = MANAGER_FOLDER + "cpy_bundles"

# For Win
URL_ROCKET_BETA = "http://api.rocket.foundation/beta/latest/"
URL_STEAM_WIN = "http://media.steampowered.com/installer/steamcmd.zip"

OUTPUT_ZIP_STEAM_WIN = MANAGER_FOLDER + "steam_temp.zip"
OUTPUT_ZIP_ROCKET = MANAGER_FOLDER + "rocket_temp.zip"

#For Linux

URL_ROCKET_LINUX = "http://api.rocket.foundation/linux-beta/latest/"
URL_STEAM_LINUX = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"

PROCNAME_WIN = "Unturned.exe"

#--Functions
def write_config(name):
    f = open(name, "w")
    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<config>
	<rebootEvery seconds="3600" />
	<unturnedFolder path=".\unturned" recoveryBundlesAfterUpdates="false" />
	<rocket useRocket="true" apikey=""/>
	<steam username="" password="" />
	<steamUpdates validate="true" />
	<servers rconEnabled="false">
		<server name="server1" rconPort="27013" rconPassword="pass" />
		<server name="server2" rconPort="27014" rconPassword="pass" />
	</servers>
	<notifyBefore seconds="60" />
</config>''')
    f.close()

def load_config(name):
    global REBOOT_TIME
    global NOTIFY_TIME
    global SERVERS_TO_LAUNCH
    global RCON_ENABLED
    global RCON_PORT
    global RCON_PASSWORD
    global UNTURNED_PATH
    global VALIDATE_AT_BOOT
    global STEAM_USER
    global STEAM_PASS
    global APIKEY
    global BACKUP_BUNDLES
    global ROCKET_ENABLED

    if (not os.path.isfile(name)):
        write_config(name)
        return True
    try:
        with open(name, 'rt') as f:
            tree = ElementTree.parse(f)

        node = tree.find("rebootEvery")
        REBOOT_TIME = int(node.attrib.get("seconds"))

        node = tree.find("steamUpdates")
        VALIDATE_AT_BOOT = node.attrib.get("validate")

        node = tree.find("unturnedFolder")
        UNTURNED_PATH = node.attrib.get("path")
        BACKUP_BUNDLES = node.attrib.get("recoveryBundlesAfterUpdates")
        if(VALIDATE_AT_BOOT != "true"):
            BACKUP_BUNDLES = "false"

        node = tree.find("rocket")
        APIKEY = node.attrib.get("apikey")
        ROCKET_ENABLED = node.attrib.get("useRocket")

        node = tree.find("steam")
        STEAM_USER = node.attrib.get("username")
        STEAM_PASS = node.attrib.get("password")

        SERVERS_TO_LAUNCH = []
        RCON_PASSWORD = []
        RCON_PORT = []
        for node in tree.iter("server"):
            SERVERS_TO_LAUNCH.append(node.attrib.get("name"))
            RCON_PORT.append(int(node.attrib.get("rconPort")))
            RCON_PASSWORD.append(node.attrib.get("rconPassword"))


        node = tree.find("servers")
        RCON_ENABLED = node.attrib.get("rconEnabled")

        node = tree.find("notifyBefore")
        NOTIFY_TIME = int(node.attrib.get("seconds"))
        if (NOTIFY_TIME > REBOOT_TIME):
            NOTIFY_TIME = REBOOT_TIME
        return False

    except:
        write_config(name)
        return True

def downloader(i):
    err = False
    if (i == "steam"):
        try:
            if (platform.system() == "Windows"):
                urllib.urlretrieve(URL_STEAM_WIN, OUTPUT_ZIP_STEAM_WIN)
            else:
                urllib.urlretrieve(URL_STEAM_LINUX, OUTPUT_ZIP_STEAM_WIN)

        except:
            err = True

    if (i == "rocket"):
        try:
            if (platform.system() == "Windows"):
                urllib.urlretrieve(URL_ROCKET_BETA + APIKEY, OUTPUT_ZIP_ROCKET)
            else:
                urllib.urlretrieve(URL_ROCKET_LINUX + APIKEY, OUTPUT_ZIP_ROCKET)
        except:
            err = True
    return err

def extractor(namezip, folder):
    zfile = zipfile.ZipFile(namezip)
    if not os.path.exists(folder):
        os.makedirs(folder)
    zfile.extractall(folder)
    zfile.close()

def clean_up():
    try:
        os.remove(OUTPUT_ZIP_STEAM_WIN)
    except:
        pass
    try:
        os.remove(OUTPUT_ZIP_ROCKET)
    except:
        pass

def installer(folder):
    try:
        for f in os.listdir(folder):
            if (not os.path.isdir(os.path.join(folder, f))):
                src_file = os.path.join(folder, f)
                dst_file = os.path.join(UNTURNED_PATH + "\\Unturned_Data\\Managed\\", f)
                shutil.copyfile(src_file, dst_file)
        return False
    except IOError:
        return True

def merge_files(root_src_dir, root_dst_dir):
    try:
        for src_dir, dirs, files in os.walk(root_src_dir):
            dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            for file_ in files:
                src_file = os.path.join(src_dir, file_)
                dst_file = os.path.join(dst_dir, file_)
                if os.path.exists(dst_file):
                    os.remove(dst_file)
                shutil.move(src_file, dst_dir)
        return False
    except:
        return True

def rcon_notify(port, passw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.settimeout(5)
    s.send("login " + passw + "\n")
    s.send("broadcast [Manager] This server will restart in " + str(NOTIFY_TIME) + " seconds\n")
    s.send("quit\n")
    s.recv(1024)

    s.close()

def rcon_shutdown(port, passw):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", port))
    s.settimeout(5)
    s.send("login " + passw + "\n")
    s.send("broadcast Rebooting...\n")
    s.send("save\n")
    s.send("shutdown\n")
    s.recv(1024)

    s.close()


def bootstrap():
    print("--------------------------------------------------------------------------------")
    print("                          SergiX44's Rocket Manager 1.8.2                       ")
    print("--------------------------------------------------------------------------------\n\n")

    print("> Creating folders...")
    if not os.path.exists(MANAGER_FOLDER):
        os.makedirs(MANAGER_FOLDER)

    print("> Loading config...")
    if load_config(MANAGER_FOLDER + "config_RocketManager.xml"):
        print("Close and edit config_RocketManager.xml, then restart me!")
        raw_input("Press any key to continue...")
        sys.exit(1)

    if not os.path.isfile("steamcmd.exe"):
        ex = True
        while ex:
            sel = raw_input("> SteamCMD not found! Would you like download it? (y/n) ")
            if sel == "y":
                print("> Downloading steamcmd...")
                if downloader("steam"):
                    print("ERROR: Unable to download steam! Please check your internet settings!")
                    raw_input("Press any key to continue...")
                    sys.exit(3)

                zfile = zipfile.ZipFile(OUTPUT_ZIP_STEAM_WIN)
                zfile.extractall()
                zfile.close()
                ex = False
            if sel == "n":
                ex = False
                print("Closing...")
                time.sleep(1)
                sys.exit(1)


def main():

    bootstrap()

    while 1:
        #reloading config
        print("> Reloading config...")
        if load_config(MANAGER_FOLDER + "config_RocketManager.xml"):
            print("> Failed loading config! :( \n"
                  "Config file regenerated, edit config_RocketManager.xml, then restart me!")
            raw_input("Press any key to continue...")
            sys.exit(2)

        #saving bundles
        if BACKUP_BUNDLES == "true":
            print("> Saving Bundles...")
            try:
                if not os.path.exists(BACKUP_BUNDLES_FOLDER):
                    os.makedirs(BACKUP_BUNDLES_FOLDER)
                if os.path.exists(BACKUP_BUNDLES_FOLDER + "\\Bundles"):
                    shutil.rmtree(BACKUP_BUNDLES_FOLDER + "\\Bundles")
                shutil.copytree(UNTURNED_PATH + "\\Bundles", BACKUP_BUNDLES_FOLDER + "\\Bundles")
            except:
                print("ERROR: Cannot saving Bundles, aborting...")

        #launch steam cmd
        if (not os.path.isdir(UNTURNED_PATH)) or (VALIDATE_AT_BOOT == "true"):
            print("> Launching SteamCMD...")
            print ("------------------------------------SteamCMD------------------------------------\n")
            os.system("steamcmd.exe +login " + STEAM_USER + " " + STEAM_PASS + " +force_install_dir " + UNTURNED_PATH + " +app_update 304930 validate +exit")
            print ("\n------------------------------------END-----------------------------------------\n\n")

        #recovering bundles
        if BACKUP_BUNDLES == "true":
            print("> Recovering Bundles...")
            if merge_files(BACKUP_BUNDLES_FOLDER + "\\Bundles", UNTURNED_PATH + "\\Bundles"):
                print("ERROR: Cannot recovering Bundles, aborting...")

        if ROCKET_ENABLED == "true":
            #download
            print("> Downloading rocket...")
            while downloader("rocket"):
                print("ERROR: Unable to download rocket! Please check your internet settings!\n"
                      "> Retrying in 5 seconds..")
                time.sleep(5)

            #extract
            print("> Extracting rocket...")
            rocket_downloaded = True
            correct_opened = True
            checkzip = None
            try:
                zzip = zipfile.ZipFile(OUTPUT_ZIP_ROCKET)
                checkzip = zzip.testzip()
                zzip.close()
            except zipfile.BadZipfile:
                correct_opened = False
            if (checkzip is None) and correct_opened:
                if os.path.exists(ROCKET_EXTRACT_FOLDER):
                    shutil.rmtree(ROCKET_EXTRACT_FOLDER)
                extractor(OUTPUT_ZIP_ROCKET, ROCKET_EXTRACT_FOLDER)
            else:
                print("> Failed to extract Rocket zip (maybe a malformed zip?)")
                if os.listdir(ROCKET_EXTRACT_FOLDER):
                    print("> Using the lastest correct download...")
                else:
                    print("> Not failover found, launching servers...")
                    rocket_downloaded = False

            #Moving files
            if rocket_downloaded:
                print("> Installing rocket...")
                if installer(ROCKET_EXTRACT_FOLDER):
                    print("> Error installing rocket, looking for opened game instances...")
                    os.system("taskkill /f /im " + PROCNAME_WIN)
                    time.sleep(1)
                    if installer(ROCKET_EXTRACT_FOLDER):
                        print("> Unable to install rocket! try to revalidate the installation!")
                        clean_up()
                        raw_input("Press any key to continue...")
                        sys.exit(4)

            #clean up zips and extracted files
            print("> Cleaning up...")
            clean_up()

        #launching servers
        print("> Launching servers...")
        for i in range(0, len(SERVERS_TO_LAUNCH)):
            print("    - Launching " + SERVERS_TO_LAUNCH[i])
            os.system("cd " + UNTURNED_PATH + "\ & start Unturned.exe -nographics -batchmode +secureserver/" +
                      SERVERS_TO_LAUNCH[i])

        #timer
        counter = REBOOT_TIME
        while counter >= 0:
            sys.stdout.write('> Waiting %s ...\r' % str(counter))
            sys.stdout.flush()
            time.sleep(1)
            counter -= 1
            if (RCON_ENABLED == "true") and (counter == NOTIFY_TIME) and (ROCKET_ENABLED == "true"):
                for i in range(0, len(RCON_PORT)):
                    try:
                        rcon_notify(RCON_PORT[i], RCON_PASSWORD[i])
                        print("    -Reboot Notified on port " + str(RCON_PORT[i]))
                    except:
                        print("    -Unable to notify the reboot on port " + str(RCON_PORT[i]) + "! Check your config!")

        if (RCON_ENABLED == "true") and (ROCKET_ENABLED == "true"):
            try:
                for i in range(0, len(RCON_PORT)):
                    rcon_shutdown(RCON_PORT[i], RCON_PASSWORD[i])
            except:
                print("> Unable to stopping the server using rcon, using the classic method...")
                os.system("taskkill /f /im " + PROCNAME_WIN)
        else:
            os.system("taskkill /f /im " + PROCNAME_WIN)


if __name__ == '__main__':
    main()
