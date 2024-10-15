from asyncio.log import logger
import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from ldap3 import Server, Connection, ALL
from django.core.exceptions import ObjectDoesNotExist
from employee.models import Employee  

class LDAPBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        ldap_server = 'localhost'
        ldap_port = 389
        base_dn = 'ou=horilla-application,dc=example,'
        admin_user = 'cn=admin,dc=example,dc=com'
        admin_password = '123'
        
        # Connect to the LDAP server
        server = Server(ldap_server, port=ldap_port, use_ssl=False, get_info=ALL)
        conn = Connection(server, admin_user, admin_password, auto_bind=True)
        
        # Search for the user in the LDAP directory
        search_filter = f'(uid={username})'
        conn.search(search_base=base_dn,
                    search_filter=search_filter,
                    search_scope='SUBTREE',
                    attributes=['givenName', 'sn', 'mail'])
        
        if len(conn.entries) == 1:
            user_entry = conn.entries[0]
            
            # Check if the password is correct
            user_dn = user_entry.entry_dn
            user_conn = Connection(server, user_dn, password, auto_bind=True)
            
            if user_conn.bind():
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User(username=username, first_name=user_entry.givenName, last_name=user_entry.sn, email=user_entry.mail)
                    user.set_password(User.objects.make_random_password())  
                    # user.set_password(password)  
                    user.save()
                
                # Ensure Employee object exists for the user
                try:
                    employee = user.employee_get
                except ObjectDoesNotExist:
                    employee = Employee.objects.create(
                        employee_user_id=user,
                        employee_first_name=user.first_name,
                        employee_last_name=user.last_name,
                        email=user.email,
                        phone="",  # Set this according to your needs
                    )

                return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None





# def sync_ldap_users():
#     ldap_server = 'localhost'
#     ldap_port = 389
#     base_dn = 'ou=horilla-application,dc=example,'
#     admin_user = 'cn=admin,dc=example,dc=com'
#     admin_password = '123'

#     # Connect to the LDAP server
#     server = Server(ldap_server, port=ldap_port, use_ssl=False, get_info=ALL)
#     conn = Connection(server, admin_user, admin_password, auto_bind=True)

#     # Search for all users in the LDAP directory
#     search_filter = '(objectClass=posixAccount)'
#     conn.search(search_base=base_dn,
#                 search_filter=search_filter,
#                 search_scope='SUBTREE',
#                 attributes=['givenName', 'sn', 'mail'])

#     for user_entry in conn.entries:
#         email = str(user_entry.mail)  
#         first_name = str(user_entry.cn)
#         last_name = str(user_entry.sn)
#         username = email.split('@')[0]  

#         try:
#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             user = User(username=username, first_name=first_name, last_name=last_name, email=email)
#             user.set_password(User.objects.make_random_password())  
#             user.save()
#             try:
#                 employee = user.employee_get
#             except ObjectDoesNotExist:
#                 employee = Employee.objects.create(
#                     employee_user_id=user,
#                     employee_first_name=user.first_name,
#                     employee_last_name=user.last_name,
#                     email=user.email,
#                     phone="", 
#                 )

#     conn.unbind()


def sync_ldap_users():
    ldap_server = 'localhost'
    ldap_port = 389
    base_dn = 'ou=horilla-application,dc=example,dc=com'
    admin_user = 'cn=admin,dc=example,dc=com'
    admin_password = '123'

    # Connect to the LDAP server
    server = Server(ldap_server, port=ldap_port, use_ssl=False, get_info=ALL)
    conn = Connection(server, admin_user, admin_password, auto_bind=True)

    # Search for all users in the LDAP directory
    search_filter = '(objectClass=posixAccount)'
    conn.search(search_base=base_dn,
                search_filter=search_filter,
                search_scope='SUBTREE',
                attributes=['givenName', 'sn', 'mail'])

    # Collect LDAP user emails for comparison
    ldap_emails = {str(user_entry.mail).lower() for user_entry in conn.entries}

    # Deactivate users in Django that are no longer in LDAP, excluding superusers
    for user in User.objects.all():
        if not user.is_superuser and user.email.lower() not in ldap_emails:
            user.is_active = False
            user.save()

    # Sync or create users from LDAP
    for user_entry in conn.entries:
        email = str(user_entry.mail).lower()  
        first_name = str(user_entry.givenName)
        last_name = str(user_entry.sn)
        username = email.split('@')[0]  

        user, created = User.objects.get_or_create(email=email, defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True,
        })

        if created:
            user.set_password(User.objects.make_random_password())
            user.save()

        # Ensure employee record is created or updated
        try:
            employee = user.employee_get
        except ObjectDoesNotExist:
            employee = Employee.objects.create(
                employee_user_id=user,
                employee_first_name=user.first_name,
                employee_last_name=user.last_name,
                email=user.email,
                phone="", 
            )

    conn.unbind()