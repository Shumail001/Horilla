import time
from django.core.management.base import BaseCommand
from horilla import sync_ldap_users  

class Command(BaseCommand):
    help = 'Sync LDAP users every 10 seconds'

    def handle(self, *args, **kwargs):
        while True:
            sync_ldap_users()
            print("Crone Job is Called")
            time.sleep(10)  
