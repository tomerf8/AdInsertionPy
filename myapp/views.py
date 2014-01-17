from django.http import HttpResponse
from django.template import RequestContext,Context, loader
from myapp.models import Media_item # Only Needed
from myutils import utils_class
from mytools import tools_class
from db_mng import db_mng_class
from django.contrib.staticfiles.views import serve
from django.shortcuts import render,render_to_response
from constants import consts
from django.core.context_processors import csrf
from django.core.servers.basehttp import FileWrapper
from datetime import datetime
import psutil
import re
import os

utils       = utils_class()
db_mng      = db_mng_class()
tools       = tools_class()

def index(request): 
    return HttpResponse("This is working")

def website(request, page="index.html"):
    utils.debug_print('Index, Requested:'+page,'flow')
    
    if page=='download.html':
        movie_list = Media_item.objects.order_by('-name')
        t = loader.get_template('download.html')
        c = Context({'movie_list':movie_list})
        return HttpResponse(t.render(c))    
    
    elif page=='upload.html':
        if request.method == 'POST':
            #Check if Ad upload
            is_ad = ( request.POST.get('is_ad') == "on" )
            
            #Save file on disk
            for key, my_file in request.FILES.items():
                match = re.search('(.*)\.',my_file.name) 
                if match:
                    file_name = match.group(1)
                else:
                    utils.debug_print('Cannot get file name','err')
                    return HttpResponse("ERROR")
                
                utils.debug_print('Uploading file '+ my_file.name,'flow')
                
                #Check if Ad

                if (is_ad):
                    path = consts.BASE_DIR+consts.PWD_UPLOADED_ADS_FILES + file_name
                else:
                    path = consts.BASE_DIR+consts.PWD_UPLOADED_MEDIA_FILES + file_name
                    
                os.system('mkdir '+path)
                file_pointer = path +'/'+ file_name
                dest = open(file_pointer, 'wb')
                if my_file.multiple_chunks:
                    for chunk in my_file.chunks():
                        dest.write(chunk)
                else:
                    dest.write(my_file.read())
                dest.close()
            
            #Handle new media
            utils.debug_print('Creating DASH for file '+ my_file.name,'flow') 
            tools.handle_new_media(path+'/',file_name , is_ad)
            
            c = RequestContext(request,{'uploadDone':True})
            c.update(csrf(request))
            return render_to_response("upload.html", c)
        else:
            c = RequestContext(request,{'uploadDone':False})
            c.update(csrf(request))
            return render_to_response("upload.html", c) 
    
    return render(request, page)

def service_algo(request,requested_hash):
    
    
    #---------------------------------------------------------------------[ Default / Init values
    
    start_time = datetime.now()
    is_pre_last_ad  = False
    valid_timestamp = True
    last_ad_viewed  = False
    
    #---------------------------------------------------------------------[ Get file name by special hash 
    
    utils.debug_print('Requested key from user: '+requested_hash,'flow')
    
    #---------------------------------------------------------------------[ Check that file mapping exist 
     
    file_mapping_obj  = db_mng.return_file_mapping_by_hash(requested_hash)
    
    if file_mapping_obj == None:
        msg = 'File Not Found, Unknown object: '+requested_hash
        utils.debug_print(msg,'err')
        return HttpResponse(msg)
    
    utils.debug_print('User name: '+file_mapping_obj.user.username,'flow')
    
    #---------------------------------------------------------------------[ Check if HASH is of an "init" file
    
    match = re.search('.*?(init)',file_mapping_obj.key)
    if match:
        user_obj  = file_mapping_obj.user
        db_mng.reinit_file_mapping(user_obj,file_mapping_obj.media)        
        return serve(request, file_mapping_obj.media.path + file_mapping_obj.file_name) 
    
    #---------------------------------------------------------------------[ Get media and user objects 
    
    media_obj                   = file_mapping_obj.media
    user_obj                    = file_mapping_obj.user
    original_file_mapping_obj   = file_mapping_obj
    redirected_file_mapping_obj = file_mapping_obj
    
    #---------------------------------------------------------------------[ Update HASH by offset (for dynamic AD insertion)

    if user_obj.global_offset:
        utils.debug_print('Global dynamic offset, '+str(user_obj.global_offset),'flow')

        redirected_hash = requested_hash[:40]+str(int(requested_hash[40:]) + user_obj.global_offset)
        utils.debug_print('Redirecting HASH to: '+redirected_hash,'flow')
        redirected_file_mapping_obj = db_mng.return_file_mapping_by_hash(redirected_hash)
        if redirected_file_mapping_obj == None:
            msg = 'File Not Found, Unknown object after adding offset'
            utils.debug_print(msg,'err')
            return HttpResponse(msg)

    #---------------------------------------------------------------------[ Check if seeking was used
    
    original_file_obj   = db_mng.return_original_media_by_name(original_file_mapping_obj.file_name) 
    redirected_file_obj = db_mng.return_original_media_by_name(redirected_file_mapping_obj.file_name) 
    
    #--[ Check if user used seeking to current request
    if consts.ENABLE_SEEKING_DETECTION:
        if (user_obj.last_req_index+1) < int(requested_hash[consts.HASH_LENGTH:]):
            utils.debug_print('User seeking detected','warn')
            utils.debug_print('Updating total durations TFDT1 after seeking TFDT1: '+str(original_file_obj.tfdt1),'flow')
            utils.debug_print('Updating total durations TFDT2 after seeking TFDT2: '+str(original_file_obj.tfdt2),'flow')
            user_obj.total_duration1 = int(original_file_obj.tfdt1,16)
            user_obj.total_duration2 = int(original_file_obj.tfdt2,16)
            user_obj.save()
        else:
            utils.debug_print('No seeking detected','flow')# change to log
    
    #--[ Check if pre last is AD
    prev_mapping = db_mng.return_file_mapping_by_hash(original_file_mapping_obj.prev_file)
    if prev_mapping != None:
        prev_prev_mapping = db_mng.return_file_mapping_by_hash(prev_mapping.prev_file)
        if prev_prev_mapping != None:
            is_pre_last_ad = prev_prev_mapping.is_ad
        
    utils.debug_print('Pre last segment was an AD: '+str(is_pre_last_ad),'flow')

    #--[ Check AD was viewed
    if consts.ENABLE_SKIP_DETECTION:
        if is_pre_last_ad:
            allowed_delta   = media_obj.segment_length
            user_time_stamp = user_obj.time_stamp
            valid_timestamp = tools.check_valid_delta(user_time_stamp,allowed_delta)
            utils.debug_print('Checking if AD was viewed: '+str(valid_timestamp),'flow')
        
            if not valid_timestamp:
                utils.debug_print('The time stamp is not valid','warn')
            else:
                last_ad_viewed = True
    else:
        if is_pre_last_ad:
            last_ad_viewed = True   
        
    #--[ Update Statistics
    is_ad_prev = tools.update_user_statistics_for_last_segment(user_obj,last_ad_viewed) 

    #--[ Check user Statistics (ratio check)
    is_ad_next = tools.check_user_stat(user_obj)      
    
    #--[ Check ratio
    if not is_ad_prev and is_ad_next:
        utils.debug_print('Next segment is ==> ***Dynamic AD***','flow')
        
        # Last file was AD ???
        user_obj.last_file_ad = True
        user_obj.global_offset -= 1
        user_obj.save()
        
        # Mark current mapping as ad
        original_file_mapping_obj.is_ad = True
        original_file_mapping_obj.save();          
        
        # add AD selection algo.
        [redirected_file_obj,relative_path] = tools.ad_selection_algo(user_obj)

    #--[ Ratio is OK, current file is not an AD => current file is a media file
    else:
        redirected_file_obj = db_mng.return_original_media_by_name(redirected_file_mapping_obj.file_name)
        utils.debug_print('Next segment is ==> ***MEDIA***: '+redirected_file_obj.file_name,'flow')
        # Last file was MEDIA
        user_obj.last_file_ad = False
        user_obj.save()
        relative_path = media_obj.path + redirected_file_obj.file_name
    
    #---------------------------------------------------------------------[ prepare file
    
    path_to_serve = tools.prepare_to_serve(relative_path,redirected_file_obj,user_obj)
    
    #---------------------------------------------------------------------[ Update durations, Update last index
    
    user_obj.total_duration1 += redirected_file_obj.duration_tfdt1
    utils.debug_print('Updating total_duration1 for next file to: '+str(user_obj.total_duration1),'flow')
    user_obj.total_duration2 += redirected_file_obj.duration_tfdt2
    utils.debug_print('Updating total_duration2 for next file to: '+str(user_obj.total_duration2),'flow')
    
    # Update last index
    user_obj.last_req_index = int(requested_hash[40:])
    user_obj.save()
    
    # Print performance
    end_time = datetime.now()
    msg = "%s\,%s\,%s\,%s\,%s\,%s"%(start_time.strftime("%H:%M:%S"),\
                         str(end_time - start_time),\
                         user_obj.username,\
                         requested_hash,\
                         str(psutil.cpu_percent()),\
                         str(psutil.virtual_memory()[2]))
    utils.print_performance(msg)
    
    utils.debug_print('Main algorithm done, Serving file to client...','flow')
    return serve(request,path_to_serve)

def direct_serv(request,requested_file):
    start_time = datetime.now()
    utils.debug_print('Requested key from user: '+requested_file,'flow')
    msg = "%s\,%s\,%s\,%s\,%s\,%s"%(start_time.strftime("%H:%M:%S"),\
                     str(datetime.now() - start_time),\
                     "Unknown",\
                     requested_file,\
                     str(psutil.cpu_percent()),\
                     str(psutil.virtual_memory()[2]))
    utils.print_performance(msg)    
    
    return serve(request,consts.PWD_MEDIA_FILES+requested_file)
 
def download_mpd(request):
    
    try:
        user  = request.GET['user']
        movie = request.GET['movie']
        ratio = request.GET['ratio']
        pref_content = request.GET['pref_content']
        msg = 'Received request for: username: %s, movie: %s, ratio: %s'%(user,movie,ratio)
        utils.debug_print(msg,'flow')
    except:
        utils.debug_print("Couldn't parse MPD request from user",'err')
        return HttpResponse('Problem with given values, check given user/movie/ratio')
    
    mpd_path = tools.create_uniqe_mpd(user,movie,ratio,pref_content)
    #return serve(request,mpd_path)
    
    # Serving Using FileWrapper!
    filename = os.path.basename(mpd_path)
    response = HttpResponse(FileWrapper(open(consts.BASE_DIR + mpd_path)))
    response['Content-Type'] = 'application/dash+xml'
    response['Content-Length'] = os.path.getsize(consts.BASE_DIR + mpd_path)
    response['Content-Disposition'] = 'attachment; filename=\"%s\"' % filename
    return response
    

def initSetup(request):
    '''========================= TEST DATA '''
    # insert new movies
    db_mng.insert_unique_media("big_buck_bunny",10000,0.3, consts.PWD_MEDIA_FILES+'big_buck_bunny/')
    db_mng.insert_unique_media("elephant_dreams",10000,0.3, consts.PWD_MEDIA_FILES+'elephant_dreams/')
    
    # insert new ads 
    db_mng.insert_unique_ad("bgu",10000,consts.PWD_AD_FILES+'bgu/')
    db_mng.insert_unique_ad("dakar",10000,consts.PWD_AD_FILES+'dakar/','sport')
    
    # scan files for movie & ad objects 
    tools.scan_mp4_files('big_buck_bunny')
    tools.scan_mp4_files('elephant_dreams')
    tools.scan_mp4_files('bgu',is_ad=True)
    tools.scan_mp4_files('dakar',is_ad=True)
    
    
    '''======================================'''
    return HttpResponse('Init complete')


