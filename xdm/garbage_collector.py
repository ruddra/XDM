# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
import os
import fnmatch
import xdm
from xdm import common
from xdm.classes import Element, Field, Image
from xdm.logger import *


def soFreshAndSoClean():
    """Runs every available clean function
    the garbage collector scheduler will call this
    """
    common.addState(6)
    try:
        # add more functions here
        cleanTemporaryElements()
        deleteOrphanElements()
        deleteOrphanFields()
        deleteOrphanImages()
        fixImages()
    except:
        raise
    finally:
        common.removeState(6)

def cleanTemporaryElements():
    log.info("Getting temp elements")
    elements_dq = Element.delete().where(Element.status == common.TEMP)
    deleted_rows = elements_dq.execute()
    log.info("Deleted %s temp elements" % deleted_rows)

def deleteOrphanFields():
    log.info("Getting orphanaged fields")
    elements = Element.select()
    fields_dq = Field.delete().where(~(Field.element << elements))
    deleted_rows = fields_dq.execute()
    log.info("Deleted %s orphanaged fields" % deleted_rows)

def deleteOrphanElements():
    log.info("Getting elements")
    elements = Element.select()
    delete_count = 0
    for element in list(elements):
        try:
            if element.parent:
                _ = element.parent
        except Element.DoesNotExist:
            log("deleting element %s" % element.get_id())
            #element.delete_instance(silent=True)
            super(Element, element).delete_instance()
            delete_count += 1

    log.info("deleted %s orphanaged elements" % delete_count)

def deleteOrphanImages():
    log.info("Getting orphanaged images")
    elements = Element.select()
    image_dq = Image.delete().where(~(Image.element << elements))
    deleted_rows = image_dq.execute()
    log.info("Deleted %s orphanaged images" % deleted_rows)

def fixImages():
    needed_files = set()
    for image in Image.select():
        path = image.getPath()
        if not os.path.isfile(path):
            log.debug("%s has no file adding it to the Q" % image)
            common.Q.put(('image.download', {'id': image.element.id}))
        needed_files.add(path)
    log.info("Needed image files %d" % len(needed_files))

    all_files = set()
    for root, dirnames, filenames in os.walk(xdm.IMAGEPATH):
        for filename in filenames:
            all_files.add(os.path.join(root, filename))

    old_files = all_files - needed_files
    log.info(u"Found image %s files " % len(all_files))
    if old_files:
        log.info(u"Removing %s old files" % len(old_files))
        for unneeded_file_path in old_files:
            unneeded_file_path = unneeded_file_path.decode("utf-8")
            log.debug(u"Deleting unneeded image file %s" % unneeded_file_path)
            os.remove(unneeded_file_path)
