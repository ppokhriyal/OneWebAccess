from flask import Blueprint,render_template,url_for, flash, redirect, request, abort, session,jsonify
from onewebaccess import app,db, bcrypt,login_manager
from onewebaccess.packagebuild.forms import PackageBuildForm
from flask_login import login_user, current_user, logout_user, login_required
from onewebaccess.models import PB
import random
import os
import os.path
from os import path
import pathlib
from pathlib import Path
import subprocess
import urllib3
import wget
import requests
import paramiko
import tarfile

#Global Paramiko variables
global client
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
blue = Blueprint('packagebuild',__name__,template_folder='templates')


@blue.route('/home')
def home():
	page = request.args.get('page',1,type=int)
	pb = PB.query.paginate(page=page,per_page=10)
	pb_count = len(db.session.query(PB).all())
	return render_template('packagebuild/home.html',title='VXL : Package Builder',pb_count=pb_count,pb=pb)

@blue.route('/new',methods=['GET','POST'])
@login_required
def build():
	form = PackageBuildForm()
	
	#PB WorkArea
	pb_pkgbuildid = random.randint(1111,9999)
	pb_pkgbuildpath = '/var/www/html/package/'+current_user.username.replace(' ','_')+'/'

	#Remove Builds which are not finished
	if not len(os.listdir(pb_pkgbuildpath)) == 0:
		for f in os.listdir(pb_pkgbuildpath):
			file = pathlib.Path(pb_pkgbuildpath+f+"/finish.true")
			if not file.exists():
				cmd = "rm -Rf "+pb_pkgbuildpath+str(f)
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()

	if form.validate_on_submit():
		#Create working directory
		os.makedirs(pb_pkgbuildpath+str(form.buildid.data))
		os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/'+str(form.osarch.data)+'/'+str(form.pkgname.data).casefold().split(':')[0])

		#Check Remote Host is Still Alive
		try:
			client.connect(str(form.remote_host_ip.data),timeout=1)
			stdin,stdout,stderr = client.exec_command("ls "+form.pkgsourcepath.data)
			if stdout.channel.recv_exit_status() != 0:
				flash(f"Please Check the remote host path",'danger')
				return redirect(url_for('packagebuild.home'))
		except Exception as ee:
			flash(f"Connection Timeout : {form.remote_host_ip.data}",'danger')
			return redirect(url_for('packagebuild.home'))

		#Start creating the squashfs file
		stdin,stdout,stderr = client.exec_command("mksquashfs "+form.pkgsourcepath.data+" "+form.pkgsourcepath.data+"/"+str(form.pkgname.data).casefold().split(':')[1]+".sq"+" "+"-e "+str(form.pkgname.data).casefold().split(':')[1]+".sq")
		#Download the newly created squashfs file
		ftp_client = client.open_sftp()
		ftp_client.get(form.pkgsourcepath.data+"/"+str(form.pkgname.data).casefold().split(':')[1]+".sq",pb_pkgbuildpath+str(form.buildid.data)+'/'+str(form.osarch.data)+'/'+str(form.pkgname.data).casefold().split(':')[0]+'/'+str(form.pkgname.data).casefold().split(':')[1]+'.sq')
		#MD5SUM Package
		cmd = "md5sum "+pb_pkgbuildpath+str(form.buildid.data)+'/'+form.osarch.data+'/'+str(form.pkgname.data).casefold().split(':')[0]+'/'+str(form.pkgname.data).casefold().split(':')[1]+'.sq'
		proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		o,e = proc.communicate()
		md5sum = o.decode('utf8')
		package_md5sum = md5sum[:32]

		#Remove sq after download
		stdin,stdout,stderr = client.exec_command("rm -rf  "+form.pkgsourcepath.data+"/"+str(form.pkgname.data).casefold().split(':')[1]+'.sq')

		#Check Patch check box is checked or not
		if form.patchboolean.data == True:
			
			#Check if Patch Fields are valid
			if len(form.patchname.data) == 0:
				flash(f"Error : Please provide Patch Name")
				return redirect(url_for('packagebuild.home'))

			#Check if Remove Packages and Install Script both are empty
			if len(form.removepkg.data) == 0 and len(form.install_script.data) == 0 and len(form.menu.data) == 0:
				flash(f"Error: Please provide Remove File/Package content or Install Script or Menu")
				return redirect(url_for('packagebuild.home'))

			#Patch is required
			#Check for patch type
			if form.patchtype.data == "Current Patch":
				#Current Patch
				#Create work area
				os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/add-pkg')
				os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root')
				#Create default findminmax script
				with open(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/findminmax.sh',"a") as f:
					f.write('#!/bin/bash')
					f.write('\n')
					f.write('mount -o remount,rw /sda1')
					f.write('\n')
					f.write('exit 0')
				#Dos2unix findminmax.sh
				subprocess.call(["dos2unix " +pb_pkgbuildpath+str(form.buildid.data)+"/Patch/root/findminmax.sh"],shell=True)
				#Copy newly creates package
				cmd = "cp -pa "+pb_pkgbuildpath+str(form.buildid.data)+'/'+str(form.osarch.data)+'/'+str(form.pkgname.data).casefold().split(':')[0]+'/'+str(form.pkgname.data).casefold().split(':')[1]+'.sq'+" "+pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/add-pkg/'+str(form.pkgname.data).casefold().split(':')[0]+':'+str(form.pkgname.data).casefold().split(':')[1]+'.sq'
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()

				#Check if menuentry is required
				if len(form.menu.data) != 0:
					menu_script = form.menu.data.split(';')
					f = open(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/install',"a+")
					f.write("#!/bin/bash")
					f.write('\n')
					f.write('mount -o rmeount,rw /sda1')
					f.write('\n')
					f.write(f"menu_entry='prog \"{menu_script[0]}\" \"{menu_script[1]}\" \"{menu_script[2]}\"'")
					f.write('\n')
					f.write(f"sed -i '/\sprog \"AnyConnect.*/a '\"$menu_entry\"'' /sda1/data/menu.orig\n")
					f.write('''cp  /sda1/data/menu.orig /data/menu.orig
cp  /sda1/data/menu.orig /data/menu
cp  /sda1/data/menu.orig /sda1/data/menu''')
					f.write('\n')
					f.write('mount -o rmeount,ro /sda1')
					f.close()

				#Check for remove packages and files
				if len(form.removepkg.data) != 0:
					os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg')
					remove_pkgs = form.removepkg.data.split(';')
					for i in remove_pkgs:
						#Check for prefix
						prefix = i.split(':',1)
						if prefix[0].casefold() not in ['core','basic','apps','boot','data','root']:
							flash(f'Missing Prefix in {prefix[0]},while removing package','danger')
							return redirect(url_for('packagebuild.home'))
						#Add delete package 
						if prefix[0].casefold() == 'core':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/core:'+prefix[1]).touch()
						if prefix[0].casefold() == 'basic':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/basic:'+prefix[1]).touch()
						if prefix[0].casefold() == 'apps':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/apps:'+prefix[1]).touch()
						if prefix[0].casefold() == 'boot':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/boot:'+prefix[1]).touch()
						if prefix[0].casefold() == 'data':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/data:'+prefix[1]).touch()
						if prefix[0].casefold() == 'root':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/sda1/data/firmware_update/delete-pkg/root:'+prefix[1]).touch()

				#Check for install script
				if len(form.install_script.data) != 0:
					install_script = form.install_script.data.split(' ')
					f = open(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/install',"a+")
					if len(form.menu.data) == 0 :
						f.write("#!/bin/bash\n")
						f.write("mount -o remount,rw /sda1")
						for i in " ".join(install_script):
							f.write(i)

						f.write("\n")
						f.write("mount -o remount,ro /sda1")    
						f.close()
					else:
						for i in " ".join(install_script):
							f.write(i)
						f.close()   

				#Dos2unix  install script
				subprocess.call(["dos2unix " +pb_pkgbuildpath+str(form.buildid.data)+"/Patch/root/install"],shell=True)

				#CHMOD
				subprocess.call(["chmod -R 755 "+pb_pkgbuildpath+str(form.buildid.data)],shell=True)

				#Build Patch Tar
				final_patch_name = form.patchname.data+'.tar.bz2'
				tar_file_path = pb_pkgbuildpath+str(form.buildid.data)+'/Patch/'+final_patch_name
				tar = tarfile.open(tar_file_path,mode='w:bz2')
				os.chdir(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/')
				tar.add(".")
				tar.close()

				#Damage Patch
				cmd = "damage corrupt "+pb_pkgbuildpath+str(form.buildid.data)+'/Patch/'+final_patch_name+" 1"
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()

				#MD5SUM Patch
				cmd = "md5sum "+pb_pkgbuildpath+str(form.buildid.data)+"/Patch/"+final_patch_name
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()
				md5sum = o.decode('utf8')
				patch_md5sum = md5sum[:32]

				#Update Database

				return redirect(url_for('packagebuild.home'))
			else:
				#Legacy Patch
				#Create work area
				os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/add-pkg')
				#Copy newly creates package
				cmd = "cp -pa "+pb_pkgbuildpath+str(form.buildid.data)+'/'+str(form.osarch.data)+'/'+str(form.pkgname.data).casefold().split(':')[0]+'/'+str(form.pkgname.data).casefold().split(':')[1]+'.sq'+" "+pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/add-pkg/'+str(form.pkgname.data).casefold().split(':')[0]+':'+str(form.pkgname.data).casefold().split(':')[1]+'.sq'
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()
				print(o)
				print(e)

				#Check if menuentry is required
				if len(form.menu.data) != 0:
					menu_script = form.menu.data.split(';')
					f = open(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/install',"a+")
					f.write("#!/bin/bash")
					f.write('\n')
					f.write('mount -o rmeount,rw /sda1')
					f.write('\n')
					f.write(f"menu_entry='prog \"{menu_script[0]}\" \"{menu_script[1]}\" \"{menu_script[2]}\"'")
					f.write('\n')
					f.write(f"sed -i '/\sprog \"AnyConnect.*/a '\"$menu_entry\"'' /sda1/data/menu.orig\n")
					f.write('''cp  /sda1/data/menu.orig /data/menu.orig
cp  /sda1/data/menu.orig /data/menu
cp  /sda1/data/menu.orig /sda1/data/menu''')
					f.write('\n')
					f.write('mount -o rmeount,ro /sda1')
					f.close()

				#Check for remove packages and files
				if len(form.removepkg.data) != 0:
					os.makedirs(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg')
					remove_pkgs = form.removepkg.data.split(';')
					for i in remove_pkgs:
						#Check for prefix
						prefix = i.split(':',1)
						if prefix[0].casefold() not in ['core','basic','apps','boot','data','root']:
							flash(f'Missing Prefix in {prefix[0]},while removing package','danger')
							return redirect(url_for('packagebuild.home'))
						#Add delete package 
						if prefix[0].casefold() == 'core':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/core:'+prefix[1]).touch()
						if prefix[0].casefold() == 'basic':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/basic:'+prefix[1]).touch()
						if prefix[0].casefold() == 'apps':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/apps:'+prefix[1]).touch()
						if prefix[0].casefold() == 'boot':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/boot:'+prefix[1]).touch()
						if prefix[0].casefold() == 'data':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/data:'+prefix[1]).touch()
						if prefix[0].casefold() == 'root':
							Path(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/firmware_update/delete-pkg/root:'+prefix[1]).touch()

				#Check for install script
				if len(form.install_script.data) != 0:
					install_script = form.install_script.data.split(' ')
					f = open(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/root/install',"a+")
					if len(form.menu.data) == 0 :
						f.write("#!/bin/bash\n")
						f.write("mount -o remount,rw /sda1")
						for i in " ".join(install_script):
							f.write(i)

						f.write("\n")
						f.write("mount -o remount,ro /sda1")    
						f.close()
					else:
						for i in " ".join(install_script):
							f.write(i)
						f.close()   

				#Dos2unix  install script
				subprocess.call(["dos2unix " +pb_pkgbuildpath+str(form.buildid.data)+"/Patch/root/install"],shell=True)

				#CHMOD
				subprocess.call(["chmod -R 755 "+pb_pkgbuildpath+str(form.buildid.data)],shell=True)

				#Build Patch Tar
				final_patch_name = form.patchname.data+'.tar.bz2'
				tar_file_path = pb_pkgbuildpath+str(form.buildid.data)+'/Patch/'+final_patch_name
				tar = tarfile.open(tar_file_path,mode='w:bz2')
				os.chdir(pb_pkgbuildpath+str(form.buildid.data)+'/Patch/')
				tar.add(".")
				tar.close()

				#Damage Patch
				cmd = "damage corrupt "+pb_pkgbuildpath+str(form.buildid.data)+'/Patch/'+final_patch_name+" 1"
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()

				#MD5SUM Patch
				cmd = "md5sum "+pb_pkgbuildpath+str(form.buildid.data)+"/Patch/"+final_patch_name
				proc = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
				o,e = proc.communicate()
				md5sum = o.decode('utf8')
				patch_md5sum = md5sum[:32]

				#Update Database

				return redirect(url_for('packagebuild.home'))
				
		else:
			#Patch is not required
			#Update Database
			update_db = PB(buildid=str(form.buildid.data),pkgname=str(form.pkgname.data).casefold().split(':')[1],description=form.description.data,osarch=form.osarch.data,md5sum_pkg=package_md5sum,pb_author=current_user)
			db.session.add(update_db)
			db.session.commit()	
			return redirect(url_for('packagebuild.home'))
			
	return render_template('packagebuild/build.html',title='VXL : Package Builder',form=form,build=pb_pkgbuildid)