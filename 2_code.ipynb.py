#!/usr/bin/env python
# coding: utf-8

# In[ ]:


##Systematic Conservation planning in Colombia: Your own Marxan Analysis


# In[78]:


#import packages
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os, re
from rasterio import open as r_open
from rasterio.plot import show as r_show 
from subprocess import Popen
from rasterstats import zonal_stats


# In[79]:


#define folder functions
def wf(x):
    return("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/" + x)
def bf(x):
    return("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps1/Colombia/processed/BioModelos/" + x)


# In[80]:


#read in municipos shapefile
mun = gpd.read_file("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/input/Municipios.shp",encoding = 'utf-8')
#subset wanted rows
mun2 = mun[~mun['COD_DEPART'].isnull()]
mun3 = mun2[~mun['COD_DEPART'].eq('88')]
#dissolve duplicate rows 
mun = mun3.dissolve(by='MUN')
#set new index
mun.index = pd.Index(range(1, len(mun) + 1), name='id') 


# In[81]:


#cost column
mun['cost'] = mun['AREA_KM']
#status column
mun['status'] = 0
#pu_dat to csv
pu_dat = mun[['cost','status']]
pu_dat.to_csv("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/input/pu.dat",index=True)
#puplayer to dat
mun[['geometry']].to_file('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/pulayer/pulayer.shp', index = True)


# In[82]:


#save to file
mun_s = mun.copy()
mun_s['geometry'] = mun_s['geometry'].simplify(0.005)
mun_s = mun_s.to_crs({'init': 'epsg:4326'})
mun_s = mun_s[['NOMBRE_ENT','geometry']]
mun_s[['geometry']].to_file('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/temp/pulayer_4326_simplified.shp')


# In[83]:


#save species file as csv 
sp = pd.read_csv("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/input/species.csv")
#set new index
sp.index = pd.Index(range(1, len(sp) + 1), name='id')
#prop column, sp
sp['prop'] = 0.3
#spf column, sp 
sp['spf']  = 1
#filter columns
sp = sp[['prop','spf','name']]
#export to csv
sp.to_csv("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/input/spec.dat", index = True)


# In[8]:


#create empty dataframe with mun and sp index
pu_x_sp = pd.DataFrame(index=mun_s.index.rename('pu'),
                       columns=sp.index.rename('species'))
pu_x_sp


# In[9]:


#for loop for coarsened raster
for sp_id, sp_name in sp['name'].iteritems ():
    print(sp_id, sp_name)
    filepath =  bf(sp_name.replace(' ','_') + '.tif') #create filepath name 
    print(filepath)
    zs = pd.DataFrame(zonal_stats(mun_s, filepath, stats = ['sum'], all_touched = True, nodata = -1)) #run zonal stats and set as dataframe
    zs.index += 1  #set index to 1
    print(zs)
    pu_x_sp.columns = pu_x_sp.columns.rename('species')
    print(pu_x_sp.columns)
    pu_x_sp[sp_id] = zs #assign output to consecutive column 
pu_x_sp


# In[84]:


#stack dataframe
puorder = pu_x_sp.stack()
#use stack to rename series 
puorder = pu_x_sp.stack().rename('amount').reset_index()
#rename columns
puorder = puorder[puorder['amount'].gt(0)][['species', 'pu', 'amount']]
#save to csv
puorder.to_csv(wf('mun/input/puorder.dat'), index=False)


# In[85]:


#convert projection from degrees to meters in mun
mun_s = mun_s.to_crs({'init': 'epsg:21818'}) #21818


# In[86]:


#convert projection from degrees to meters in mun
mun = mun.to_crs({'init': 'epsg:21818'}) #21818


# In[87]:


#empty bound list for storage 
bound_list = []


# In[88]:


#for loop for computing boundaries of touching polygons
from itertools import combinations
for id1, id2 in combinations(mun.index, 2): #combination loop 
    print(id1,id2)
    geom1 = mun.loc[id1]['geometry']    #get geom for id1 and id2
    geom2 = mun.loc[id2]['geometry']  
    geom_new = geom1.intersection(geom2) #intersect with geom2          
    if geom_new.is_empty == False:     #check to see if there is intersection; if geom is not empty then record boundary length
        boundary = geom_new.length     #record boundary of shared length
        bound_list += [[id1, id2, boundary]]    #cast to a boundary list 
        bound = pd.DataFrame(bound_list, columns =  ['id','id2','boundary']) #save boundary list to bound variable as dataframe


# In[89]:


#select boundaries that were recorded as 0 and remove
bound2 = bound[bound.boundary != 0]


# In[90]:


#save boundary file
bound2.to_csv(wf('mun/input/bound.dat'), index=False)


# In[91]:


#define filepath
def tf(x):
    return("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/output/" + x)


# In[93]:


#load in colombia outline change to 21818 crs
outline = gpd.read_file('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/outline/Colombia_outline_GADM.shp')
outline = outline.to_crs({'init': 'epsg:4686'})


# In[122]:


#run marxan again with set parameters
def run_marxan(folder):
    import os 
    marxan_command = './MarOpt_v243_Mac64'
    os.chdir(folder)
    return Popen(marxan_command).wait()
run_marxan(wf('mun'))


# In[123]:


from matplotlib.colors import LinearSegmentedColormap
cmap_dict = {'red':   [(0.0,  1.0, 1.0),
                       (1.0,  0.06, 0.06)],
             'green': [(0.0,  1.0, 1.0),
                       (1.0,  0.25, 0.25)],
             'blue':  [(0.0,  1.0, 1.0),
                       (1.0,  0.98, 0.98)]}
my_cmap = LinearSegmentedColormap('', cmap_dict)


# In[124]:


#selection output
output_ssoln = gpd.read_file('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/output/output_ssoln.csv')
output_ssoln.index = pd.Index(range(1, len(mun) + 1), name = 'id')
output_join = mun.merge(output_ssoln, on = 'id') #join back to mun for geography
output_join = gpd.GeoDataFrame(output_join, geometry = 'geometry_x')  #set geom and geodataframe
output_join = output_join.to_crs({'init': 'epsg:4686'}) #change crs


# In[125]:


#convert numbers to a int
output_join['number']=output_join['number'].astype(int)
#outputs that were just zero 
output_zero = output_join[output_join.number == 0]
#outputs that are non-zero
output_full = output_join[output_join.number != 0]


# In[126]:


#plot map
fig, ax = plt.subplots()
#set x, y limits
xlim = ([-79.00903163,-66.8472154])
ylim = ([-4.22593577, 12.45944319 ])
ax.set_xlim(xlim)
ax.set_ylim(ylim)
color = '#4adfcf'
output_full.plot('number',ax = ax ,cmap = my_cmap, edgecolor = 'none', linewidth=0,legend =True)
outline.plot(ax = ax, color = 'none',edgecolor = 'black' , linewidth = 1)
output_zero.plot(ax=ax, color ='cyan')
fig.set_size_inches(15,15)
ax.set_title('Selection Frequency Colombia (BLM = .01, EPSG:21818)', pad = 15, fontsize = 20)
plt.savefig('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/deliverables/2_selection_frequency_colombia.png',bbox_inches='tight',dpi=150)


# In[ ]:


####MODIFYING YOUR ASSUMPTIONS


# In[127]:


#switch mun_s to 4326 crs
mun_s = mun_s.to_crs({'init': 'epsg:4326'})


# In[128]:


#perform zonal stat on data
zs_travel = pd.DataFrame(zonal_stats(mun_s, 
                        '/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/travel/accessibility_to_cities_col.tif', 
                        stats = ['mean'], all_touched = False, nodata = -9999 ))



# In[129]:


zs_travel['mean'].value_counts()


# In[130]:


#set zs index
zs_travel.index = pd.Index(range(1, len(mun_s) + 1), name = 'id')
#change to int
zs_travel['mean']=zs_travel['mean'].astype(int)
#take out stuff I dont need
mun_x = mun[['NOMBRE_ENT','geometry','AREA_KM']]
#join with mun_x
mun_x = mun_x.merge(zs_travel, on = 'id')
mun_x['mean']=mun_x['mean'].astype(int)
#compute cost
mun_x['cost'] = mun_x['AREA_KM']*(mun_x['mean']**-0.5)
#status column
mun_x['status'] = 0
pu_dat = mun_x[['cost','status']]
pu_dat.to_csv("/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/input/pu.dat",index=True)


# In[140]:


#run marxan again with set parameters
def run_marxan(folder):
    import os 
    marxan_command = './MarOpt_v243_Mac64'
    os.chdir(folder)
    return Popen(marxan_command).wait()
run_marxan(wf('mun'))


# In[141]:


#selection output
output_ssoln = gpd.read_file('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/Colombia/mun/output/output_ssoln.csv')
output_ssoln.index = pd.Index(range(1, len(mun) + 1), name = 'id')
output_join = mun.merge(output_ssoln, on = 'id') #join back to mun for geography
output_join = gpd.GeoDataFrame(output_join, geometry = 'geometry_x')  #set geom and geodataframe
output_join = output_join.to_crs({'init': 'epsg:4686'}) #change crs
#convert numbers to a int
output_join['number']=output_join['number'].astype(int)
#outputs that were just zero 
output_zero = output_join[output_join.number == 0]
#outputs that are non-zero
output_full = output_join[output_join.number != 0]


# In[143]:


#plot map
fig, ax = plt.subplots()
#set x, y limits
xlim = ([-79.00903163,-66.8472154])
ylim = ([-4.22593577, 12.45944319 ])
ax.set_xlim(xlim)
ax.set_ylim(ylim)
color = '#4adfcf'
output_full.plot('number',ax = ax ,cmap = my_cmap, edgecolor = 'none', linewidth=0,legend =True)
outline.plot(ax = ax, color = 'none',edgecolor = 'black' , linewidth = 1)
output_zero.plot(ax=ax, color ='cyan')
fig.set_size_inches(15,15)
ax.set_title('Selection Frequency Colombia: Travel time (BLM = .000001, EPSG:21818)', pad = 15, fontsize = 20)
plt.savefig('/Users/christianabys/Desktop/School/Boston_University/2020/Data_Science/ps2/deliverables/2_selection_frequency_colombia_traveltime.png',bbox_inches='tight',dpi=150)


# In[ ]:




