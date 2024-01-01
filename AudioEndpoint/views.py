from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import AudioResponseSerializer


class AudioUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        if 'file' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        audio_file = request.data['file']
        # TODO: Process the audio file using commented out functions above

        # TODO: Get get from vector db
        floating_point_number = 3.30

        # TODO: Change to processed audio file
        response_data = {
            'file': audio_file,
            'floating_point_number': floating_point_number
        }
        serializer = AudioResponseSerializer(data=response_data)

        if serializer.is_valid():
            # TODO: save? do additional processing here?
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
