#
# Copyright (C) 2023, Dojo Five
# All rights reserved.
#

import os
import cbor2
import random
from collections.abc import Callable
from ..ble_client import BLEClient
from .ble_smp_service import *


DFU_HASH_SIZE        = 64   # Size of session hash, in bits
DFU_CHUNK_SIZE       = 128  # Size of image chunk sent over SMP payload


class BLEDFUService(BLESMPService):

    """A service for performing device image management over SMP."""

    def __init__(self, client: BLEClient):

        """
        Construct a new BLEDFUService object.
        """

        super().__init__(client)

    async def get_state_of_images(self, verbose=True):

        """Performs a request over SMP to get the state of images. The format of the response can be found
        `here <https://docs.zephyrproject.org/latest/services/device_mgmt/smp_groups/smp_group_1.html#get-state-of-images-response>`

        :return: Response object as dictionary
        """

        header = BLESMPService._get_smp_header(OP_READ, 0, GRP_IMAGE_MANAGEMENT, 0, IMAGE_STATE_COMMAND)

        rsp = await self.write_smp_and_response(bytearray(header))

        if verbose:
            print("%s: Retrieving partitions state..." % (__class__.__name__))
            self.print_state_of_images(rsp)

        return rsp

    async def set_state_of_image(self, hash_str: str, confirm: bool, verbose=True):

        """Performs a request over SMP to set the state of an image.

        More information:
        https://docs.zephyrproject.org/latest/services/device_mgmt/smp_groups/smp_group_1.html#set-state-of-image-request

        :param hash_str: Hash of image to set the state of

        :param confirm: If “confirm” is false or not provided, an image with the “hash” will be set for test,
            which means that it will not be marked as permanent and upon hard reset the previous application will be
            restored to the primary slot. In case when “confirm” is true, the “hash” is optional as the currently running
            application will be assumed as target for confirmation.

        :return: Response object as dictionary
        """

        cbor_data = {"hash": hash_str, "confirm": confirm}
        payload = list(cbor2.dumps(cbor_data))

        header = BLESMPService._get_smp_header(OP_WRITE, len(payload), GRP_IMAGE_MANAGEMENT, 0, IMAGE_STATE_COMMAND)

        rsp = await self.write_smp_and_response(bytearray(header + payload))

        if verbose:
            print("%s: Setting partitions state..." % (__class__.__name__))
            self.print_state_of_images(rsp)

        return rsp

    async def image_upload(self, image_path: str, on_update: Callable[[int, int], None] = None) -> bool:

        """Upload an image to the second image slot of the device. This method will upload the entire image which
        could take several minutes depending on the size of the image.

        :param image_path: Absolute path to the image binary file (relative paths may not work correctly)

        :return: Status of operation (True on success, False on error)
        :rtype: bool
        """

        if not os.path.isfile(image_path):
            print("%s: invalid path" % (self.__class__.__name__))
            return False

        offset = 0
        hash_str = str(random.getrandbits(DFU_HASH_SIZE))
        image_total_size = os.path.getsize(image_path)
        image_size_kB = round((image_total_size / 1000), 2)
        image_num = 1

        print(f"{self.__class__.__name__}: Starting DFU for {os.path.basename(image_path)} ({image_size_kB} kB)...")

        while offset != image_total_size:

            # Send the first chunk
            payload = self._build_image_upload_payload(image_num, image_path, offset, image_total_size, hash_str)
            header_bytes = BLESMPService._get_smp_header(OP_WRITE, len(payload), GRP_IMAGE_MANAGEMENT, 0, IMAGE_UPLOAD_COMMAND)

            rsp = await self.write_smp_and_response(bytearray(header_bytes + payload))

            offset = rsp["off"]

            if on_update:
                on_update(offset, image_total_size)

        print(f"{self.__class__.__name__}: Completed DFU of {os.path.basename(image_path)}...")

        return True

    async def erase_image(self, slot: int):

        """
        Erase an image by slot and return the response.

        :param slot: Slot of image to erase (usually 1, the DFU slot)

        :return: Response object as dictionary
        """

        header = BLESMPService._get_smp_header(OP_WRITE, 0,  GRP_IMAGE_MANAGEMENT, 0, IMAGE_ERASE_COMMAND)

        cbor_data = {"slot": slot}
        payload = list(cbor2.dumps(cbor_data))

        rsp = await self.write_smp_and_response(bytearray(header + payload))
        return rsp

    @staticmethod
    def print_state_of_images(rsp):

        """
        Prints the status of of the image partitions

        :param rsp: Image management retrieved from the SMP header buffer
        """

        slot_0_version   = "-"
        slot_0_hash      = "-"
        slot_0_bootable  = "-"
        slot_0_pending   = "-"
        slot_0_confirmed = "-"
        slot_0_active    = "-"
        slot_0_permanent = "-"

        slot_1_version   = "-"
        slot_1_hash      = "-"
        slot_1_bootable  = "-"
        slot_1_pending   = "-"
        slot_1_confirmed = "-"
        slot_1_active    = "-"
        slot_1_permanent = "-"

        for image in rsp['images']:
            if image['slot'] == 0:
                slot_0_version      = image['version'  ]
                slot_0_hash         = image['hash'     ].hex().upper()[:6] + "..."
                slot_0_bootable     = image['bootable' ]
                slot_0_pending      = image['pending'  ]
                slot_0_confirmed    = image['confirmed']
                slot_0_active       = image['active'   ]
                slot_0_permanent    = image['permanent']
            if image['slot'] == 1:
                slot_1_version      = image['version'  ]
                slot_1_hash         = image['hash'     ].hex().upper()[:6] + "..."
                slot_1_bootable     = image['bootable' ]
                slot_1_pending      = image['pending'  ]
                slot_1_confirmed    = image['confirmed']
                slot_1_active       = image['active'   ]
                slot_1_permanent    = image['permanent']

        print(f"-----------------------------------------")
        print(f"------------ PARTITION STATE ------------")
        print(f"-----------------------------------------")
        print(f"****** SLOT 0 ******|****** SLOT 1 ******")
        print(f"version   {slot_0_version   : <9} | version   {slot_1_version   : <9}")
        print(f"hash      {slot_0_hash      : <9} | hash      {slot_1_hash      : <9}")
        print(f"bootable  {slot_0_bootable  : <9} | bootable  {slot_1_bootable  : <9}")
        print(f"pending   {slot_0_pending   : <9} | pending   {slot_1_pending   : <9}")
        print(f"confirmed {slot_0_confirmed : <9} | confirmed {slot_1_confirmed : <9}")
        print(f"active    {slot_0_active    : <9} | active    {slot_1_active    : <9}")
        print(f"permanent {slot_0_permanent : <9} | permanent {slot_1_permanent : <9}")
        print(f"-----------------------------------------")

    @staticmethod
    def get_image_version(image_path: str) -> tuple[int, int, int, int] | None:

        """Return the version of an MCU boot update binary.

        :return: Version as a tuple of (major, minor, revision, build num), None if parsing failed or image doesn't exist
        """

        # Follows the image_header struct within Zephyr
        # NRF_SDK/bootloader/mcuboot/boot/bootutil/include/bootutil/image.h
        IMAGE_HEADER_SIZE    = 32   # Size of the image header, in bytes
        IMAGE_VERSION_OFFSET = 20   # Number of bytes until the start of the image_version struct
        IMAGE_VERSION_SIZE   = 8    # Number of bytes in image header struct

        if not os.path.isfile(image_path):
            return None

        try:
            with open(image_path, "rb") as image_file:

                header_bytes = image_file.read(IMAGE_HEADER_SIZE)
                version_bytes = header_bytes[IMAGE_VERSION_OFFSET : IMAGE_VERSION_OFFSET+IMAGE_VERSION_SIZE]

                # Follows the image_version struct within Zephyr
                # NRF_SDK/bootloader/mcuboot/boot/bootutil/include/bootutil/image.h
                major     = int.from_bytes(version_bytes[0]  , byteorder="little")
                minor     = int.from_bytes(version_bytes[1]  , byteorder="little")
                revision  = int.from_bytes(version_bytes[2:4], byteorder="little")
                build_num = int.from_bytes(version_bytes[4:] , byteorder="little")

                return (major, minor, revision, build_num)

        except:
            return None

    def _build_image_upload_payload(self, image_num: int, image_path: str, offset: int, image_total_size: int, hash_str: str):

        """
        Internal function to build an SMP payload for the image upload
        """

        with open(image_path, mode="rb") as file:
            file.seek(offset)
            read_size = min(DFU_CHUNK_SIZE, image_total_size - offset)
            file_data = file.read(read_size)

            cbor_data = {}

            cbor_data["image"] = image_num
            cbor_data["len"] = image_total_size
            cbor_data["off"] = offset
            cbor_data["sha"] = bytes(hash_str.encode('utf-8'))
            cbor_data["data"] = bytes(file_data)
            cbor_data["upgrade"] = False

            return list(cbor2.dumps(cbor_data))
