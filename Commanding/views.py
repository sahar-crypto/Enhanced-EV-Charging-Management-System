from Commanding.models import Transaction
from Charging.models import EVCharger
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from decimal import Decimal
from django.http import JsonResponse



@login_required
def send_remote_command(request, charger_id):
    command = request.GET.get('command')
    amount = request.GET.get('amount', None)  # Optional

    try:
        charger = EVCharger.objects.get(ID=charger_id)
    except EVCharger.DoesNotExist:
        return JsonResponse({'error': 'Charger not found'}, status=404)

    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            f'charging_station_{charger_id}',
            {
                'type': 'send_command',
                'command': command
            }
        )
    except Exception as e:
        return JsonResponse({'error': f'Failed to send command: {str(e)}'}, status=500)

    # Save the transaction ONLY if sending succeeded
    Transaction.objects.create(
        user=request.user,
        command=command,
        amount=Decimal(amount) if amount else None,
        charger=charger
    )

    return JsonResponse({'message': 'Command sent and saved successfully'})

