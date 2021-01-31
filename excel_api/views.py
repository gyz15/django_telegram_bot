from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ApiUser, Plan

# Create your views here.


class FindStocks(APIView):
    def get(self, request, format=None):
        print(request.headers)
        if 'API-Key' in request.headers:
            user = ApiUser.objects.filter(key=request.headers['API-Key'])
            if user.exists():
                user = user[0]
                # return data here
                # if user still have chance today
                return Response({'Test': 'Hello World'}, status=status.HTTP_200_OK)
            else:
                return Response({'Error': 'Key invalid'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'Error': 'Key Not Included'}, status=status.HTTP_400_BAD_REQUEST)
