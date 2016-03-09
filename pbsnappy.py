#!/usr/bin/env python
#
# pbsnappy - automatically make volume snapshots for ProfitBricks server 
# Copyright (C) 2016 Gerben Meijer
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#

from datetime import datetime, timedelta
import config
from slugify import slugify
from pprint import pprint

from profitbricks.client import ProfitBricksService
client = ProfitBricksService( username=config.PB_USERNAME, password=config.PB_PASSWORD) 


# Get the PB Datacenter object
datacenter = client.get_datacenter(datacenter_id=config.DATACENTER_ID)

# Get a list of snapshots; this is global so can be done here
snapshots = client.list_snapshots()

# Process all found entities (servers) in 
for entity in datacenter['entities']['servers']['items']:
  # If this entity is not a server, continue (could be gateway, loadbalancer etc)
  if not entity['type'] == 'server':
   continue

  # Get this entitys server object from API
  server = client.get_server(datacenter_id=config.DATACENTER_ID,server_id=entity['id'])

  # Set the servername
  servername = server['properties']['name']

  # If this server is listed in our config, do the work
  if servername in config.TARGET_SERVER_NAMES:

    # Get the list of volumes for this server
    for server_volume in server['entities']['volumes']['items']:
  
     # Set volumeid
     volumeid = server_volume['id']

     # Get the volume object from API

     volume = client.get_volume( datacenter_id=config.DATACENTER_ID,volume_id=volumeid)
     # Set the volumename
     volumename = volume['properties']['name']

     # Assume we have no recent snapshots 
     no_recent_snapshot = True

     # find snapshots that have a name starting with this volumename
     for snapshot in snapshots['items']:
      # Set the snapid and snapname
      snapid = snapshot['id']
      snapname = snapshot['properties']['name']

      # Convert the snapshot createdDate to snapdate datetime object
      snapdate = datetime.strptime(snapshot['metadata']['createdDate'], "%Y-%m-%dT%H:%M:%SZ")

      # Check that the snapshot name starts with the target server name
      # We do this in a for loop because we have to check string startswith()
      if(snapname.startswith(volumename)):

        # We have a match on snapshot name related to this volumename
        # Check if it's outdated and ready for deletion
        if (datetime.utcnow() - snapdate) > timedelta(days=config.RETENTION_DAYS):
        
         # Too old, delete it
         client.delete_snapshot(snapshot_id=snapid)
         print "Server '%s' snapshot '%s' deleted, older than %d retention days" % (servername, snapname, config.RETENTION_DAYS)
        else:
         # Recent, keep it
         print "Server '%s' snapshot '%s' kept, not older than %d retention days" % (servername, snapname, config.RETENTION_DAYS)
         
	 # For recent backups, check if it's less than min_snap_hours 
	 snapage = datetime.utcnow() - snapdate
         if snapage < timedelta(hours=config.MIN_SNAP_HOURS):
	  # Snapshot is recent, don't make a new one
          no_recent_snapshot = False


    # Does this volume have recent snapshots?
    if no_recent_snapshot:

      # nothing recent, create one. Following PB default name syntax, e.g. "{volumename}-Snapshot-MM/DD/YYYY"
      snapname = volumename + '-Snapshot-' + datetime.utcnow().strftime('%m/%d/%Y')

      # Do the actual snapshot creation api call
      newsnapshot = client.create_snapshot(datacenter_id=config.DATACENTER_ID,volume_id=volumeid, name=snapname)
      print "Created new snapshot '%s' with id '%s'" % (snapname, newsnapshot['id'])
    else:

     # No need to make a snapshot, we have a recent one
     print "Found snapshot less than %d hours old, not making new one" % config.MIN_SNAP_HOURS

  else: 

    # This server is not managed based on config settings
    print "Not managing snapshots for %s" % servername
