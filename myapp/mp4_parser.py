
'''
Created on Apr 26, 2013

@author: mrklin
'''
from myutils import utils_class
from mytools import tools_class
import os
import re

tools = tools_class()
utils = utils_class()
ad_path    = '/home/mrklsin/Temp/mayo/'
media_path = '/home/mrklin/Temp/car/' 


def scan_mp4_files(path):    
    # check for list in path
    output = commands.getoutput('ls '+path)
    file_list = output.split('\n')
    
    # Scan files
    file_dict = {}
    for file_name in file_list:
        # make sure files are m4s
        if '.m4s' not in file_name:
            continue
    
        res = tools.get_mp4_data(path + file_name)
        # check file search of TFDT ok
        if res != {}:
            # Try to get segment number
            match = re.search(".*?([0-9]+).m4s",file_name)
            if match:
                segmnet_num  = match.group(1)
                res['full_path']     = path + file_name
                res['file_name']     = file_name
                file_dict[int(segmnet_num)] = res               
    
    return file_dict

def copy_tfdt_src_to_dst(src_data,dst_data): 
    utils.debug_print('Updating TFDT from '+src_data['full_path']+' to '+dst_data['full_path'],'log')
    tools.change_mp4_data(src_data['full_path'],src_data['tfdt1'],dst_data['tfdt1'])
    tools.change_mp4_data(src_data['full_path'],src_data['tfdt2'],dst_data['tfdt2'])
    utils.debug_print('Done updating TFDT','log')

def insert_comercial_to(ad_dict, all_media_dict, segmnet_num):
    # Insert ad
    utils.debug_print('Updating TFDT of ad','log')
    if segmnet_num in all_media_dict:
        copy_tfdt_src_to_dst(ad_dict,all_media_dict[segmnet_num])
    
    while (segmnet_num in all_media_dict) :
        curr_file = all_media_dict[segmnet_num]
        # Calculate new offset of TFDT1/2
        new_tfdt1 = tools.make_tfdt_header(curr_file['tfdt1'],ad_dict['tfdt1_offset'])
        new_tfdt2 = tools.make_tfdt_header(curr_file['tfdt2'],ad_dict['tfdt2_offset'])
        # Update the files
        tools.change_mp4_data(curr_file['full_path'],curr_file['tfdt1'],new_tfdt1)
        tools.change_mp4_data(curr_file['full_path'],curr_file['tfdt2'],new_tfdt2)
        segmnet_num += 1    
    
    
    
    
    '''# update all following
    utils.debug_print('Updating TFDT of files after ad')
    while (segmnet_num in all_media_dict) and ((segmnet_num+1) in all_media_dict):
        copy_tfdt_src_to_dst(all_media_dict[segmnet_num], all_media_dict[segmnet_num+1])
        segmnet_num += 1
     
    utils.debug_print('Updating TFDT of last file')   
    # Fix last segmnet'''
    


import commands
if __name__ == '__main__':

    # Scan both dirs
    ad_dict                 = scan_mp4_files(ad_path)
    ad_dict[1]['tfdt1_offset'] = '192512'
    ad_dict[1]['tfdt2_offset'] = '109000'
    media_dict              = scan_mp4_files(media_path)
    import pdb;pdb.set_trace()
    # Update the rest of the files
    insert_comercial_to(ad_dict[1], media_dict, 4)
    
    
    
