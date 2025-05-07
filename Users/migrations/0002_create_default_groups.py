from django.db import migrations

def create_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    User = apps.get_model('Users', 'User')

    group_permissions = {
        'admin': [
            'add_user', 'change_user', 'delete_user', 'view_user',
            'add_organization', 'change_organization', 'delete_organization', 'view_organization',
            'add_customer', 'change_customer', 'delete_customer', 'view_customer',
            'add_paymentmethod', 'change_paymentmethod', 'delete_paymentmethod', 'view_paymentmethod',
            'change_invoice', 'delete_invoice', 'view_invoice',
            'add_evcharger', 'change_evcharger', 'delete_evcharger', 'view_evcharger',
            'add_station', 'change_station', 'delete_station', 'view_station',
            'change_transaction', 'delete_transaction', 'view_transaction',
            'view_statuslog',
        ],
        'organization': [
            'add_user',
            'add_organization',
            'add_evcharger', 'view_evcharger',
            'add_station', 'view_station',
            'view_transaction', 'view_statuslog',
        ],
        'customer': [
            'add_user',
            'add_customer',
            'add_paymentmethod',
            'view_evcharger', 'view_station', 'view_transaction',
        ],
    }

    for group_name, perm_codes in group_permissions.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        for code in perm_codes:
            perm = Permission.objects.filter(codename=code).first()
            if perm:
                group.permissions.add(perm)
            else:
                print(f"[WARNING] Permission '{code}' not found.")
        group.save()

class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions),
    ]