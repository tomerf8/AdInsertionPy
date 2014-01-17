from myapp.models import *
from myutils import utils_class

utils   = utils_class()


class db_mng_class(object):
    '''
    classdocs
    '''
    
    def __init__(self):
        pass
    
    #==== File mapping
    
    def return_file_obj_by_key(self,key):
        obj = File_mapping.objects.get(pk=key)
        return obj
        
    def return_file_mapping_by_hash(self,_hash):
        try:  
            obj = File_mapping.objects.get(pk=_hash)
        except:
            obj = None

        return obj
    
    def reinit_file_mapping(self,user_obj,media_item):
        utils.debug_print('Init all Values','flow')
        user_obj.total_duration1    = 0
        user_obj.total_duration2    = 0
        user_obj.media_ctr          = 0
        user_obj.ad_ctr             = 1
        user_obj.global_offset      = 0
        user_obj.last_req_index     = 0
        user_obj.last_file_ad       = False
        user_obj.save()

        file_mapping_list = File_mapping.objects.filter(user = user_obj,media = media_item )
        for file_mapping in file_mapping_list:    
            file_mapping.is_ad = False
            file_mapping.save()
    
    
    def return_original_media_by_name(self,name):
        obj = Original_media_item.objects.get(pk=name)
        return obj
    
    def return_original_ad_by_name(self,name):
        obj = Original_ad_item.objects.get(pk=name)
        return obj

    def return_user_obj_by_key(self,user_name):
        obj = Users.objects.get(pk=user_name)
        return obj
    
    #==== Media
    
    def insert_unique_media(self,name,segment_length,allowed_ratio,path):
        '''
        @summary: creates a Media item in the database
        '''
        try:
            Media_item.objects.get(name = name)
            utils.debug_print('name: '+name+' already in DATABASE','warn')
        except:
            mi = Media_item(name            = name,\
                            segment_length  = segment_length,\
                            allowed_ratio   = allowed_ratio,\
                            path            = path)
            mi.save()
    
    def return_media_key_by_name(self,name):
        obj = Media_item.objects.get(name=name)
        return obj   
    
    #==== Ad
    
    def insert_unique_ad(self,name,segment_length,path,content_type = 'random'):
        try:
            Ad_item.objects.get(name = name)
            utils.debug_print('name: '+name+' already in DATABASE','warn')
        except:
            ad = Ad_item(name            = name,\
                         segment_length  = segment_length,\
                         path            = path,\
                         content_type    = content_type)
            ad.save()
    
    def return_ad_key_by_name(self,name):
        obj = Ad_item.objects.get(name=name)
        return obj 
    
    def return_all_original_ads(self,pref_content):
        '''
        @summary: Return all Ads and filter by pref_content
        @param pref_content: Type of ad content
        '''
        if pref_content == 'random':
            all_obj = Ad_item.objects.all()
        else:
            all_obj = Ad_item.objects.filter(content_type = pref_content)
        return all_obj
    
    #==== Original_media_item
    
    def save_original_files_by_dict(self,file_dict,predecessor_obj,is_ad=False):
        '''
        @summary: by a given dictionary that holds data about the files
        enters them to the SQL database
        @param file_dict: dictionary that holds data about the files
        @param media_obj: SQL object of media
        @param is_ad: True if file is an ad
              False if file is a media file
        '''
        #==[ Save to SQL
        all_segments  = file_dict.keys()
        last = True
        last_tfdt1 = 0
        last_tfdt2 = 0
        for segment_num in sorted(all_segments, reverse = True):
            
            #utils.debug_print('inserting : '+str(file_dict[int(segment_num)])+' to DATABASE','log')
            # Check if last file
            if last:
                duration_tfdt1 = -1
                duration_tfdt2 = -1
                last = False
            else:
                duration_tfdt1 = last_tfdt1 - int(file_dict[int(segment_num)]['tfdt1'],16)
                duration_tfdt2 = last_tfdt2 - int(file_dict[int(segment_num)]['tfdt2'],16)
            
            # Create a new Original_media_item object
            if is_ad:
                new_file = Original_ad_item(file_name           = file_dict[int(segment_num)]['file_name'],\
                                               ad               = predecessor_obj,\
                                               tfdt1            = file_dict[int(segment_num)]['tfdt1'],\
                                               tfdt2            = file_dict[int(segment_num)]['tfdt2'],\
                                               offset_tfdt1     = file_dict[int(segment_num)]['tfdt1_offset'],\
                                               offset_tfdt2     = file_dict[int(segment_num)]['tfdt2_offset'],\
                                               duration_tfdt1   = duration_tfdt1,\
                                               duration_tfdt2   = duration_tfdt2,\
                                               index            = str(segment_num),\
                                               )
            # File is a Media file
            else:
                new_file = Original_media_item(file_name     = file_dict[int(segment_num)]['file_name'],\
                                            media            = predecessor_obj,\
                                            tfdt1            = file_dict[int(segment_num)]['tfdt1'],\
                                            tfdt2            = file_dict[int(segment_num)]['tfdt2'],\
                                            offset_tfdt1     = file_dict[int(segment_num)]['tfdt1_offset'],\
                                            offset_tfdt2     = file_dict[int(segment_num)]['tfdt2_offset'],\
                                            duration_tfdt1   = duration_tfdt1,\
                                            duration_tfdt2   = duration_tfdt2,\
                                            index            = str(segment_num),\
                                            )
            new_file.save()
            
            # Save last TFDT
            last_tfdt1 = int(file_dict[int(segment_num)]['tfdt1'],16)
            last_tfdt2 = int(file_dict[int(segment_num)]['tfdt2'],16)
            
    def return_media_duration(self,file_mapping_obj):
        '''
        @summary: Returns media duration of file given file mapping object
        @return: dictionary
        @param file_mapping_obj: file_mapping_obj
        '''
        if file_mapping_obj.is_ad == False:
            temp = self.return_original_media_by_name(file_mapping_obj.file_name)
        else:
            temp = self.return_original_ad_by_name(file_mapping_obj.file_name)
        
        return {'dur1' : temp.duration_tfdt1 , 'dur2': temp.duration_tfdt2}
        
        
        
        
        
        
        
         
            
            
            