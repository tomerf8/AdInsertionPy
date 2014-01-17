
from myapp.models import *
from datetime import datetime
from django.utils import timezone
from constants import consts
from myutils import utils_class
from db_mng import db_mng_class

import re
import os
import binascii
import commands
import hashlib
import random

db_mng  = db_mng_class()
utils   = utils_class()

class tools_class:
     
    def __init__(self,):
        pass
    
    #========================[ MPD
    
    def create_uniqe_mpd(self,user,movie,ratio,pref_content='random'):
        '''
        @summary: Creating a special MPD for a user based on:
                  SHA1( user_name + movie_name+random_number(1000) )
                  and create specific file mapping in our DB
        @param user:  user name
        @param movie: movie name
        @param ratio: ratio as float string
        @param pref_content: Preffarable user ad content
        '''
        # Create new user
        utils.debug_print('Creating user: '+user,'log')
        user_obj = Users(username = user,password = user+'pass',ratio = float(ratio),\
                         pref_content = pref_content)
        user_obj.save()
        
        # Create file mapping
        utils.debug_print('Creating file mapping for: '+movie,'log')
        uniq_hash = hashlib.sha1(user+movie+str(random.randrange(10000))).hexdigest()
        self.create_file_mapping(user_obj,movie,uniq_hash,ratio)
        
        # Copy template MPD
        original_mpd_name = movie + '_dash.mpd'
        new_name = 'temp_mpd'+datetime.now().strftime("%Y-%m-%d_%H:%M:%S")+'.mpd'
        new_path = consts.BASE_DIR + consts.PWD_TEMP_MPD  + new_name
        src_path = consts.BASE_DIR + consts.PWD_MPD_FILES + original_mpd_name
        
        utils.debug_print('New Path+filename Created '+new_path,'log')      
        cmd = 'sed \'s/HASH/%s/g;s/ADDRESS/%s/g\' %s > %s'\
                %(uniq_hash,consts.SERVER_IP+':'+consts.SERVER_PORT,src_path,new_path)

        os.system(cmd)
        # Return MPD
        return consts.PWD_TEMP_MPD + new_name


        
    def create_file_mapping(self,user_obj,media_item_name,uniq_hash,user_ratio=''):
        '''
        @summary: create a file mapping in the Database for a MEDIA item
        @param user_obj: user object reference
        @param media_item_name: a string which holds the media item name
        @param uniq_hash: special hash given for each user
        '''
        utils.debug_print('Creating file mapping for user: '+user_obj.username+' MEDIA name: '+media_item_name,'flow')

        media_obj = Media_item.objects.get(name = media_item_name)
        # Define ratio 
        if user_ratio == '':
            ratio = media_obj.allowed_ratio
        else:
            ratio = float(user_ratio)
        print ratio
        all_original_media = media_obj.myMediaOriginals.order_by("index")
        hash_ctr  = 1
        prev_mapping_key = None
        for file_item in all_original_media:
            # Insert Media file
            utils.debug_print('Creating file mapping for MEDIA file: '+file_item.file_name +' @'+str(hash_ctr),'flow')
            temp = File_mapping(key         = uniq_hash+str(hash_ctr),\
                                file_name   = file_item.file_name,\
                                user        = user_obj,\
                                media       = media_obj,\
                                is_ad       = False,\
                                prev_file   = prev_mapping_key)
            temp.save()
            prev_mapping_key = temp.key
            hash_ctr  += 1          
            
        # Insert empty slots at the end (for dynamic ad insertion)
        for i in xrange(int(len(all_original_media)*(ratio+1))):
            utils.debug_print('Creating empty file mapping'+' @'+str(hash_ctr),'flow')
            temp = File_mapping(key         = uniq_hash+str(hash_ctr),\
                                file_name   = 'a new ad',\
                                user        = user_obj,\
                                media       = media_obj,\
                                is_ad       = True,\
                                prev_file   = prev_mapping_key)
            temp.save()
            hash_ctr += 1
            prev_mapping_key = temp.key           
        
        # Insert Init file 
        temp = File_mapping(key         = uniq_hash+'init',\
                            file_name   = media_item_name+'_dashinit.mp4',\
                            user        = user_obj,\
                            media       = media_obj,\
                            is_ad       = False)
        temp.save()
        return hash_ctr
                
    #========================[ MP4 Control
    
    def parse_mp4_data(self,path):
        '''
        @summary: get value in hex of TFDT mp4 header
        @param path: path to MP4 file
        @return: dictionary with keys 'tfdt1' and 'tfdt2'
        '''
        # Open the file
        try:
            utils.debug_print('analyzing file '+path,'flow')
            f = open(path,'rb')
            # Initialize
            found_count = 0
            match_list = ['t','f','d','t']
            ctr = 0
            res = {}
            offset = 0
            
            res = {'tfdt1':'0','tfdt2':'0','tfdt1_offset':'0','tfdt2_offset':'0',}
            while found_count != 2:
                # Check that there is something to read
                byte_s = f.read(1)
                offset += 1
                # If end of file
                if not byte_s:
                    break
                byte = byte_s[0]
                    
                # Check if match
                if byte == match_list[ctr]:
                    ctr += 1
                else:
                    ctr = 0   
                
                # Check if done
                if ctr == 4:
                    found_count += 1
                    temp_val = f.read(8)
                    temp_val_str = binascii.b2a_hex(temp_val)
                    res['tfdt'+str(found_count)] = temp_val_str
                    int_value = str(int('0x'+temp_val_str,0))
                    utils.debug_print('found TFDT value '+ temp_val_str+' int value '+int_value,'log')
                    offset += 8
                    res['tfdt'+str(found_count)+'_offset'] = str(offset)
                    utils.debug_print('found TFDT offset '+ str(offset),'log')
                    ctr = 0
            # Solve issue with last segment
            if found_count == 0:
                utils.debug_print('Didn\'t find TFDT headers on file','err')
            elif found_count == 1:
                utils.debug_print('Didn\'t found TFDT2 on file: '+path+' valid only if this is the last segment','warn')

            return res
        except:
            utils.debug_print('Failed to get DATA tfdt','err')  
            return {}
        finally:
            utils.debug_print('closing file','log')
            f.close() 
    
    def switch_mp4_tfdt(self,path,old_value,new_value):
        '''
        @summary: change mp4 fields given an old value
        @param path: path to MP4 file
        @param old_value: old TFDT value as ASCII
        @param new_value: new TFDT value as ASCII
        @return: None
        '''
        now = datetime.now()
        # Open the file

        try:
            utils.debug_print('opening file to switch TFDT: ' + path,'log')
            f = open(path,'rb')
            text = f.read()
            f.close()
            utils.debug_print("tfdt_old "+old_value+" tfdt_new "+new_value,'log')
            text = text.replace("tfdt"+old_value,"tfdt"+new_value, 1);
            f = open(path,'wb')
            utils.debug_print('writing TFDT to file','log')
            f.write(text)
        except Exception,e:
            print e
            utils.debug_print('Failed to replace DATA tfdt','err')
            return {}
        finally:
            utils.debug_print('closing file','log')
            if f:
                f.close()
            utils.debug_print('TFDT took Micro seconds: '+str((datetime.now()-now).microseconds),'log')
            
            
    def calc_ascii_tfdt_header(self,old_tfdt,offset):
        '''
        @summary: add offset to old_tfdt value and return value in a formated form
                  for example: 0x\x00\x00\x00\x00\x00\x08\xf0\x00
        @param old_tfdt: string such as 0x\x00\x00\x00\x00\x00\x08\xf0\x00
        @param offset: the offset as string / integer
        @return: a new TFDT header in a format 0x\x00\x00\x00\x00\x00\x08\xf0\x00
        '''
        old_tfdt  = binascii.b2a_hex(old_tfdt)
        new_value = int(old_tfdt,16)+int(offset)
        new_value =  "%x" % new_value
        ascii_val = binascii.a2b_hex(new_value.zfill(16))
        # print binascii.b2a_hex(ascii_val)
        return ascii_val
        
    def scan_mp4_files(self,predecessor_name,is_ad=False):
        '''
        @summary: This function scans all files in a folder,
                  the path is extracted from media_obj.path
                  and enters them to the database
        @param predecessor_name: name of Media / Ad predecessor object
        @param is_ad: True if file is an ad
                      False if file is a media file
        '''
        # find media path
        if is_ad:
            predecessor_obj = db_mng.return_ad_key_by_name(predecessor_name)
            if str(predecessor_obj.myAdOriginals.order_by("index")) != '[]':
                utils.debug_print('The files for object: '+predecessor_name+' already in database canceling scan','warn')
                return 1
        else:
            predecessor_obj = db_mng.return_media_key_by_name(predecessor_name)
            if str(predecessor_obj.myMediaOriginals.order_by("index")) != '[]':
                utils.debug_print('The files for object: '+predecessor_name+' already in database canceling scan','warn')
                return 1
            
        # check for list in path
        path = consts.BASE_DIR + predecessor_obj.path
        output = commands.getoutput('ls '+path)
        file_list = output.split('\n')
        
        # Check folder not empty
        if file_list == []:
            return 1
        
        #==[ Scan files
        file_dict = {}
        for file_name in file_list:
            # make sure files are m4s
            if '.m4s' not in file_name:
                continue
        
            tfdt_field_dict = self.parse_mp4_data(path + file_name)
            # check file search of TFDT ok
            if tfdt_field_dict != {}:
                # Try to get segment number
                match = re.search(".*?([0-9]+).m4s",file_name)
                if match:
                    segmnet_num  = match.group(1)
                    tfdt_field_dict['file_name'] = file_name
                    file_dict[int(segmnet_num)]  = tfdt_field_dict               
        
        #==[ Save to SQL
        db_mng.save_original_files_by_dict(file_dict,predecessor_obj,is_ad)

    def prepare_to_serve(self,relative_path,current_file_obj,user_obj):
        '''
        @summary: Prepare file to serve in real-time
                    1) Copy file to temp
                    2) Update tfdt
                    3) serve
        @param relative_path: consts.<...>/file_name
        @param current_file_obj: file obj of original media
        @param user_obj: user obj
        '''   
        
        new_name = 'temp_' + user_obj.username + '_' +datetime.now().strftime("%d_%H:%M:%S")
        new_path = consts.BASE_DIR + consts.PWD_TEMP_FILES + new_name 
        full_path = consts.BASE_DIR + relative_path
        
        utils.debug_print('New Path+filename Created '+new_path,'log')      
        utils.debug_print('copy command: '+'cp '+full_path +' '+ new_path,'log')
        
        os.system('cp '+full_path +' '+ new_path)
        
        # Make ASCII TFDT from durations
        new_tfdt1 = self.calc_ascii_tfdt_header('\x00', user_obj.total_duration1)
        new_tfdt2 = self.calc_ascii_tfdt_header('\x00', user_obj.total_duration2)
        
        # Fix from HEX to ASCII current file duration
        old_tfdt1 = current_file_obj.tfdt1
        old_tfdt2 = current_file_obj.tfdt2    
        old_tfdt1 = self.calc_ascii_tfdt_header('\x00', int(old_tfdt1,16))
        old_tfdt2 = self.calc_ascii_tfdt_header('\x00', int(old_tfdt2,16))
        
        utils.debug_print('Changing TFDT update of '+new_path,'flow')
        
        self.switch_mp4_tfdt(new_path,old_tfdt1,new_tfdt1)
        self.switch_mp4_tfdt(new_path,old_tfdt2,new_tfdt2)
                
        utils.debug_print('Done TFDT updating','flow')
        
        return consts.PWD_TEMP_FILES + new_name 
        
    #========================[ Statistics
    
    def update_user_statistics_for_last_segment(self,user_obj,last_ad_viewed=False):
        '''
        @summary: increments users counter according to the last file viewed 
        @param user_obj: sql object of user 
        @return: true -last segment was an ad
                 false-last segment was a media file
        '''
        if last_ad_viewed:
            utils.debug_print('The last file user viewed was an ad','flow')
            user_obj.ad_ctr = user_obj.ad_ctr + 1
            utils.debug_print('New ad counter: '+str(user_obj.ad_ctr),'flow')
        elif user_obj.last_file_ad == False:
            utils.debug_print('The last file user viewed was a media file','log')
            user_obj.media_ctr = user_obj.media_ctr + 1
            utils.debug_print('New media counter: '+str(user_obj.media_ctr),'flow')

        user_obj.time_stamp = datetime.now()
        user_obj.save()
        utils.debug_print('Updating user time stamp to: '+ str(user_obj.time_stamp),'flow')
        return user_obj.last_file_ad 
    
    def check_user_stat(self,user_obj):
        '''
        @summary: check and calculates user statistics
        @param user_obj: sql object of user 
        @return: True -the next segment should be an ad
                 False-the next segment should be a media file 
        '''
        ratio = float(user_obj.ad_ctr) / float(user_obj.media_ctr)
        utils.debug_print('Current ratio for user: '+str(ratio),'flow')
        return user_obj.ratio > ratio

        
    #========================[ Data transfer
    
    def download_content_from_client(self):
        pass
    
    def download_ad_from_client(self):
        pass
   
    def handle_new_media(self,path,file_name,is_ad):
        '''
        @summary: Add a new uploaded file to database, create MPD
        @param path: Uploaded file path
        @param file_name:  File name
        @param is_ad:  Boolean Flag
        '''
        # Create DASH
        os.system('cd '+path+' && MP4Box -dash 10000 -profile live ' + file_name)
        
        if (is_ad):
            # No need to edit MPD..
            db_mng.insert_unique_ad(file_name,10000,consts.PWD_UPLOADED_ADS_FILES+file_name+'/')
            self.scan_mp4_files(file_name,is_ad)
        else:    
            # Edit MPD
            src = path + file_name+'_dash.mpd'
            dst = consts.BASE_DIR + consts.PWD_MPD_FILES +file_name+'_dash.mpd'
            
            try:
                f = open(src,'r')
                mpd = f.read()
                f.close()
                mpd = mpd.replace('.mp4','')
                mpd = mpd.replace('.m4s','')
                mpd = mpd.replace(file_name+'_dash','HASH')
                mpd = mpd.replace('</ProgramInformation>','</ProgramInformation><BaseURL>http://'\
                                  +consts.SERVER_IP+':'+consts.SERVER_PORT+'/myapp/site_media/</BaseURL>')
                f = open(dst,'w')
                f.write(mpd)
                f.close()
                
                # insert new movies
                db_mng.insert_unique_media(file_name,10000,0.3, consts.PWD_UPLOADED_MEDIA_FILES+file_name+'/')
                self.scan_mp4_files(file_name)
            except:
                utils.debug_print('Error Open MPD for Reading','flow')
            
    
    #========================[ Logic unit
    
    def check_valid_delta(self,user_time_stamp,allowed_delta):
        '''
        @summary: Check if the time between the last chunk was downloaded is valid
        @param user_time_stamp: the last time a user tried to download a file (datetime obj)
        @param allowed_delta: the maximum allowed delta for this media (datetime obj)  
        @return: true -enough time has passed
                 false-not enough time has passed
        '''
        # calculate delta in milliseconds
        delta = datetime.now() - user_time_stamp        
        delta_ms = delta.total_seconds() * 1000 + consts.ALOWED_DELTA_DEVIATION_MS
        
        utils.debug_print('Delta: '+str(delta)+' delta_ms: '+str(delta_ms)+' allowed delta: '+str(allowed_delta),'flow')

        if delta_ms < allowed_delta:
            # delta is too small
            return False
        else :
            # delta is ok 
            return True   

    def ad_selection_algo(self,user_obj):
        '''
        @summary: make a random selection of an AD chooses the first file 
                  in a randomly selected AD
        @param user_obj: user obj
        @return: [original AD object, relative path+file name of first file in the list]
        '''
        
        all_ads         = db_mng.return_all_original_ads(user_obj.pref_content)
        random_ad_item  = random.choice(all_ads)
        ad_name         = random_ad_item.name+'_dash1.m4s'
        relative_path   = random_ad_item.path + ad_name
        orig_ad_obj     = db_mng.return_original_ad_by_name(ad_name)
        
        return orig_ad_obj,relative_path
        
    

