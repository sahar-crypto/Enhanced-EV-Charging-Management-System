from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class SendCommandAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, station_code):
        command = request.data.get('command')
        target_charger = request.data.get('target_charger')

        if not command or not target_charger:
            return Response({'error': 'Missing command or target_charger'}, status=status.HTTP_400_BAD_REQUEST)

        group_name = f'ev_station_{station_code}'
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_command',
                'command': command,
                'target_charger': target_charger,
            }
        )
        return Response({'status': 'command sent'}, status=status.HTTP_200_OK)
