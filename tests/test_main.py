# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import logging
import subprocess
import os
import shutil
import time
import datetime
from tests.testutils import TestUtils
from click.testing import CliRunner
from lycheesync.sync import main

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean")
@pytest.mark.usefixtures("initdb_and_fs")
@pytest.mark.usefixtures("confborg")
@pytest.mark.usefixtures("initloggers")
class TestClass:

    def check_grand_total(self, expected_albums, expected_photos):

        tu = TestUtils()
        assert (tu.count_db_albums() == expected_albums), "there should be {} albums in db".format(
            expected_albums)
        assert (tu.count_db_photos() == expected_photos), "there should be {} photos in db".format(
            expected_photos)
        # assert Number of photo / thumbnail on filesystem
        # assert Number of photo / thumbnail on filesystem
        assert tu.count_fs_thumb() == expected_photos
        assert tu.count_fs_photos() == expected_photos

    def test_env_maker(self):
        tu = TestUtils()
        # clean all
        upload_path = os.path.join(tu.conf['lycheepath'], '/uploads')
        if os.path.exists(upload_path):
            shutil.rmtree(upload_path)
        tu.drop_db()
        tu.make_fake_lychee_db()
        tu.make_fake_lychee_fs(tu.conf['lycheepath'])
        # file system exists
        assert os.path.exists(os.path.join(tu.conf['lycheepath'], 'uploads', 'big'))
        assert os.path.exists(os.path.join(tu.conf['lycheepath'], 'uploads', 'medium'))
        assert os.path.exists(os.path.join(tu.conf['lycheepath'], 'uploads', 'thumb'))
        # table exists
        assert tu.table_exists('lychee_albums')
        assert tu.table_exists('lychee_photos')

    def test_subdir(self):
        try:
            tu = TestUtils()
            # copy directory to tmptest
            tu.load_photoset("album2")

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -d -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # assert Number of album / photos in database
            expected_albums = 3
            expected_photos = 4
            assert (tu.count_db_albums() == expected_albums), "there should be {} albums in db".format(
                expected_albums)
            assert (tu.count_db_photos() == expected_photos), "there should be {} photos in db".format(
                expected_photos)
            # assert Number of photo / thumbnail on filesystem
            assert tu.count_fs_thumb() == expected_photos
            assert tu.count_fs_photos() == expected_photos

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_duplicate(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # copy directory to tmptest
            tu.load_photoset("album2")

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # re-run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # assert Number of album / photos in database
            expected_albums = 3
            expected_photos = 4
            assert (tu.count_db_albums() == expected_albums), "there should be {} albums in db".format(
                expected_albums)
            assert (tu.count_db_photos() == expected_photos), "there should be {} photos in db".format(
                expected_photos)
            # assert Number of photo / thumbnail on filesystem
            # assert Number of photo / thumbnail on filesystem
            assert tu.count_fs_thumb() == expected_photos
            assert tu.count_fs_photos() == expected_photos
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_album_date(self):
        # album date should be equal to date/time original
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load album x and y
            tu.load_photoset("real_date")

            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.album_exists_in_db("real_date")
            # read album date for album1
            album1_date = tu.get_album_creation_date('real_date')

            real_date = datetime.datetime.fromtimestamp(album1_date)
            theorical_date = datetime.datetime(2011, 11, 11, 11, 11, 11)

            assert (real_date == theorical_date), "album date is 2011/11/11 11:11:11"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_dash_r(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load album x and y
            tu.load_photoset("album1")
            tu.load_photoset("album3")

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -r -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.album_exists_in_db("album1")
            # read album date for album1
            album1_date = tu.get_album_creation_date('album1')
            # read album date for album3
            album3_date = tu.get_album_creation_date('album3')

            # empty tmp pictures folder
            tu.delete_dir_content(src)

            tu.dump_table('lychee_albums')
            # sleep 1 s to make time album signature different
            time.sleep(2)

            # load album3
            tu.load_photoset("album3")

            # run
            cmd = 'python main.py {} {} {} -r -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            album1_date_2 = tu.get_album_creation_date('album1')
            album3_date_2 = tu.get_album_creation_date('album3')
            tu.dump_table('lychee_albums')
            # y date < time
            assert album1_date == album1_date_2, 'album 1 is untouched'
            assert tu.check_album_size('album1') == 1

            # x date > time
            assert album3_date < album3_date_2, 'album 3 has been modified'
            assert tu.check_album_size('album3') == 4

            expected_albums = 2
            expected_photos = 5
            self.check_grand_total(expected_albums, expected_photos)

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_dash_d(self):
        try:
            # load album y
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load album x and y
            tu.load_photoset("album1")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -r -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.check_album_size("album1") == 1, "album 1 not correctly loaded"

            # clean input pics content
            tu.delete_dir_content(src)
            # load album x
            tu.load_photoset("album3")

            # run
            cmd = 'python main.py {} {} {} -v -d'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.check_album_size("album3") == 4, "album 3 not correctly loaded"
            # album 1 has been deleted
            a1_check = tu.album_exists_in_db("album1")
            assert not(a1_check), "album 1  still exists"

            expected_albums = 1
            expected_photos = 4
            self.check_grand_total(expected_albums, expected_photos)

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    # without -s albums id should not be sorted by name
    def test_dash_wo_s(self):
        try:
            # -s => no album reorder
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load a bunch of album
            tu.load_photoset("aaa")
            tu.load_photoset("mini")
            tu.load_photoset("zzzz")
            tu.load_photoset("album1")
            tu.load_photoset("album3")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # get a_id, a_names
            list = tu.get_album_ids_titles()
            logger.info(list)
            # album name sorted

            # id sorted
            ids = sorted([x['id'] for x in list])
            titles = sorted([x['title'] for x in list])

            logger.info(ids)
            logger.info(titles)

            # combine
            ordered_list = zip(ids, titles)
            logger.info(ordered_list)
            # for each sorted
            well_sorted = True
            for x in ordered_list:
                logger.info(x)

                if (tu.get_album_id(x[1]) != x[0]):
                    well_sorted = False

            assert (not well_sorted), "elements should not be sorted"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    # with the -s switch album ids should be sorted by album title
    def test_dash_s(self):
        try:
            # -s => no album reorder
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load a bunch of album
            tu.load_photoset("aaa")
            tu.load_photoset("mini")
            tu.load_photoset("zzzz")
            tu.load_photoset("album1")
            tu.load_photoset("album3")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -s -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # get a_id, a_names
            list = tu.get_album_ids_titles()
            logger.info(list)
            # album name sorted

            # id sorted
            ids = sorted([x['id'] for x in list])
            titles = sorted([x['title'] for x in list])

            logger.info(ids)
            logger.info(titles)

            # combine
            ordered_list = zip(ids, titles)
            logger.info(ordered_list)
            # for each sorted
            for x in ordered_list:
                assert (tu.get_album_id(x[1]) == x[0]), "element not ordered " + x[1]

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_dash_l(self):
        try:
            # load album y
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load album x and y
            tu.load_photoset("album1")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']
            # -l => symbolic links instead of files

            # run
            cmd = 'python main.py {} {} {} -l -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # check if files are links
            dest = os.path.join(lych, "uploads", "big")
            not_dir = [x for x in os.listdir(dest) if not(os.path.isdir(x))]
            for f in not_dir:
                full_path = os.path.join(dest, f)
                assert os.path.islink(full_path), "this file {} is not a link".format(full_path)

        except AssertionError:
            raise
            assert False
        except Exception as e:
            logger.exception(e)
            assert False

    def test_unicode(self):
        try:
            # there is a unicode album
            # there is a unicode photo
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load unicode album name
            tu.load_photoset("FußÄ-Füße")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.count_fs_photos() == 2, "photos are missing in fs"
            assert tu.count_db_photos() == 2, "photos are missing in db"
            assert tu.album_exists_in_db("FußÄ-Füße"), "unicode album is not in db"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_corrupted(self):
        try:
            # load 1 album with a corrupted file
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load unicode album name
            tu.load_photoset("corrupted_file")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # no import
            assert tu.count_fs_photos() == 0, "there are photos are in fs"
            assert tu.count_db_photos() == 0, "there are photos are in db"
            assert tu.album_exists_in_db("corrupted_file") == 1, "corrupted_album not in db"
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_empty_album(self):
        try:
            # load 1 empty album
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load unicode album name
            tu.load_photoset("empty_album")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # no import
            assert tu.count_fs_photos() == 0, "there are photos are in fs"
            assert tu.count_db_photos() == 0, "there are photos are in db"
            assert not(tu.album_exists_in_db("empty_album")), "empty_album in db"
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_long_album(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # get max_width column album name width
            maxwidth = tu.get_column_width("lychee_albums", "title")
            logger.info("album title length: " + str(maxwidth))
            # create long album name
            dest_alb_name = 'a' * (maxwidth + 10)
            assert len(dest_alb_name) == (maxwidth + 10)

            # copy album with name
            tu.load_photoset("album1", dest_alb_name)

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # there is a max_width album
            albums = tu.get_album_ids_titles()
            alb_real_name = albums.pop()["title"]
            assert len(alb_real_name) == maxwidth, "album len is not " + str(maxwidth)

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_sha1(self):
        """
        Should also trigger a warn
        duplicates containes photos from album1
        """
        try:
            tu = TestUtils()
            retval = subprocess.call("ls /tmp/lychee/uploads/big", shell=True)
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            retval = subprocess.call("ls /tmp/lychee/uploads/big", shell=True)
            logger.warn("!!!!!!!!!!!!!!!!!!! %s", tu.count_fs_photos())
            retval = subprocess.call("ls /tmp/lychee/uploads/big", shell=True)
            # load 1 album with same photo under different name
            tu.load_photoset("album1")
            # load 2 album with same photo under different name
            tu.load_photoset("duplicates")

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            # no duplicate
            assert tu.count_db_albums() == 2, "two albums not created"
            assert tu.count_fs_photos() == 2, "there are duplicate photos in fs"
            assert tu.count_db_photos() == 2, "there are duplicate photos in db"
            assert tu.count_fs_thumb() == 2, "there are duplicate photos in thumb"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_album_keep_original_case(self):
        try:
            # load 1 album with a mixed case name and spaces
            # name in db is equal to directory name
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("album1", "AlBum_One")

            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.count_db_albums() == 1, "two albums created"
            assert tu.count_fs_photos() == 1, "there are duplicate photos in fs"
            assert tu.count_db_photos() == 1, "there are duplicate photos in db"
            assert tu.count_fs_thumb() == 1, "there are duplicate photos in thumb"
            assert tu.get_album_id("AlBum_One"), 'there is no album with this name'
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_bad_taketime(self):
        try:
            # load "bad taketime"  album name
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("invalid_takedate")
            launch_date = datetime.datetime.now()
            time.sleep(1)
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.count_db_albums() == 1, "two albums created"
            assert tu.count_fs_photos() == 1, "there are duplicate photos in fs"
            assert tu.count_db_photos() == 1, "there are duplicate photos in db"
            assert tu.count_fs_thumb() == 1, "there are duplicate photos in thumb"
            creation_date = tu.get_album_creation_date("invalid_takedate")
            creation_date = datetime.datetime.fromtimestamp(creation_date)
            assert creation_date > launch_date, "creation date should be now"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_invalid_taketime(self):
            # load "bad taketime"  album name
        tu = TestUtils()
        assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
        # load 1 album with same photo under different name
        tu.load_photoset("invalid_taketime")

        src = tu.conf['testphotopath']
        lych = tu.conf['lycheepath']
        conf = tu.conf['conf']

        # run
        cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
        logger.info(cmd)
        retval = -1
        retval = subprocess.call(cmd, shell=True)
        # no crash
        assert (retval == 0), "process result is ok"

        assert tu.count_db_albums() == 1, "too much albums created"
        assert tu.count_fs_photos() == 1, "there are duplicate photos in fs"
        assert tu.count_db_photos() == 1, "there are duplicate photos in db"
        assert tu.count_fs_thumb() == 1, "there are duplicate photos in thumb"

    def test_quotes_in_album_name(self):
        # load "bad taketime"  album name
        tu = TestUtils()
        assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
        # load 1 album with same photo under different name
        tu.load_photoset("with'\"quotes")

        src = tu.conf['testphotopath']
        lych = tu.conf['lycheepath']
        conf = tu.conf['conf']

        # run
        cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
        logger.info(cmd)
        retval = -1
        retval = subprocess.call(cmd, shell=True)
        # no crash
        assert (retval == 0), "process result is ok"

        assert tu.count_db_albums() == 1, "too much albums created"
        assert tu.count_fs_photos() == 1, "there are duplicate photos in fs"
        assert tu.count_db_photos() == 1, "there are duplicate photos in db"
        assert tu.count_fs_thumb() == 1, "there are duplicate photos in thumb"

    def test_photoid_equal_timestamp(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("album3")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']
            # normal mode
            before_launch = datetime.datetime.now()
            time.sleep(1.1)

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            time.sleep(1.1)
            after_launch = datetime.datetime.now()
            photos = tu.get_photos(tu.get_album_id('album3'))
            for p in photos:
                logger.info(p)
                # substract 4 last characters
                ts = str(p['id'])[:-4]

                # timestamp to date
                dt = datetime.datetime.fromtimestamp(int(ts))
                logger.info(dt)
                assert after_launch > dt, "date from id not < date after launch"
                assert dt > before_launch, "date from id not > date before launch"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_shutter_speed(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("rotation")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            photos = tu.get_photos(tu.get_album_id('rotation'))
            for p in photos:
                if p['title'] == 'P1010319.JPG':
                    assert p['shutter'] == '1/60 s', "shutter {} not equal 1/60 s".format(p['shutter'])
                    assert p['focal'] == '4.9 mm', "focal {} not equal 4.9 mm".format(p['focal'])
                    assert p['iso'] == '100', "iso {} not equal 100".format(p['iso'])
                    assert p['aperture'] == 'F3.3', "aperture {} not equal F3.3".format(p['aperture'])
                if p['title'] == 'P1010328.JPG':
                    assert p['shutter'] == '1/30 s', "shutter {} not equal 1/30 s".format(p['shutter'])
                    assert p['focal'] == '4.9 mm', "focal {} not equal 4.9 mm".format(p['focal'])
                    assert p['iso'] == '400', "iso {} not equal 400".format(p['iso'])
                    assert p['aperture'] == 'F3.3', "aperture {} not equal F3.3".format(p['aperture'])
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    def test_rotation(self):
        try:
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("rotation")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']
            logger.error("!!!!!!!!!!!!!!!!! %s", conf)

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            photos = tu.get_photos(tu.get_album_id('rotation'))
            for p in photos:
                pass
        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False

    @pytest.mark.xfail
    def test_sanity_check(self):
        assert False

    def test_visually_check_logs(self):
        try:
            # load "bad taketime"  album name
            tu = TestUtils()
            assert tu.is_env_clean(tu.conf['lycheepath']), "env not clean"
            # load 1 album with same photo under different name
            tu.load_photoset("invalid_takedate")
            tu.load_photoset("album2")
            tu.load_photoset("album3")
            tu.load_photoset("corrupted_file")
            tu.load_photoset("duplicates")
            # launch lycheesync
            src = tu.conf['testphotopath']
            lych = tu.conf['lycheepath']
            conf = tu.conf['conf']

            # run
            cmd = 'python main.py {} {} {} -v'.format(src, lych, conf)
            logger.info(cmd)
            retval = -1
            retval = subprocess.call(cmd, shell=True)
            # no crash
            assert (retval == 0), "process result is ok"

            assert tu.count_db_albums() == 7, "too much albums created"
            assert tu.count_fs_photos() == 10, "there are duplicate photos in fs"
            assert tu.count_db_photos() == 10, "there are duplicate photos in db"
            assert tu.count_fs_thumb() == 10, "there are duplicate photos in thumb"

        except AssertionError:
            raise
        except Exception as e:
            logger.exception(e)
            assert False
