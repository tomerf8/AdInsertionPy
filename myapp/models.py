from django.db import models
from datetime import timedelta
from django.utils import timezone

'''
Declare DB Models, Source of Data
'''

#====================[ Users
class Users(models.Model):
    username        = models.CharField(max_length=500,primary_key = True)
    password        = models.CharField(max_length=500)
    #time_stamp       = models.DateTimeField('time stamp',null=True, blank=True,default=timezone.now()-timedelta(days=2))
    time_stamp      = models.DateTimeField('time stamp',null=True, blank=True,default=timezone.now())
    ad_ctr          = models.IntegerField(default=1)
    media_ctr       = models.IntegerField(default=0) # for first segment stat. update
    global_offset   = models.IntegerField(default=0)
    last_file_ad    = models.BooleanField(default=False)
    total_duration1 = models.BigIntegerField(default=0)
    total_duration2 = models.BigIntegerField(default=0)
    last_req_index  = models.IntegerField(default=0)
    ratio           = models.FloatField(default=0)
    pref_content    = models.CharField(max_length=500)  
    
    def __unicode__(self):
        return self.username

#====================[ Media Item
class Media_item(models.Model):
    name           = models.CharField(max_length=500,primary_key = True)
    segment_length = models.IntegerField(default=0)
    allowed_ratio  = models.FloatField(default=0)
    path           = models.CharField(max_length=500)
    
    def __unicode__(self):
        return self.name.replace('_',' ')

#====================[ Ad Item
class Ad_item(models.Model):
    name           = models.CharField(max_length=500,primary_key = True)
    segment_length = models.IntegerField(default=0)
    path           = models.CharField(max_length=500)
    content_type   = models.CharField(max_length=500)
    
    def __unicode__(self):
        return self.name

#====================[ Orginal Media files
class Original_media_item(models.Model):
    file_name       = models.CharField(max_length=500,primary_key = True)
    index           = models.IntegerField(default=-1)
    media           = models.ForeignKey(Media_item,related_name='myMediaOriginals', null=True)
    tfdt1           = models.CharField(max_length=500)
    tfdt2           = models.CharField(max_length=500)
    offset_tfdt1    = models.CharField(max_length=500)
    offset_tfdt2    = models.CharField(max_length=500)
    duration_tfdt1  = models.IntegerField(default=0)
    duration_tfdt2  = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.file_name

#====================[ Orginal Ad files
class Original_ad_item(models.Model):
    file_name       = models.CharField(max_length=500,primary_key = True)
    index           = models.IntegerField(default=-1)
    ad              = models.ForeignKey(Ad_item,related_name='myAdOriginals', null=True)
    tfdt1           = models.CharField(max_length=500)
    tfdt2           = models.CharField(max_length=500)
    offset_tfdt1    = models.CharField(max_length=500)
    offset_tfdt2    = models.CharField(max_length=500)
    duration_tfdt1  = models.IntegerField(default=0)
    duration_tfdt2  = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.file_name
    
#====================[ File Mapping
class File_mapping(models.Model):
    key       = models.CharField(max_length=500,primary_key = True) #HASH
    file_name = models.CharField(max_length=500)
    user      = models.ForeignKey(Users, null=True)
    media     = models.ForeignKey(Media_item,null=True)
    is_ad     = models.BooleanField(default=False)
    prev_file = models.CharField(max_length=500, null=True)
    
    def __unicode__(self):
        return self.key +'   /   '+ self.file_name




