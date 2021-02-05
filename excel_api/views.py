from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ApiUser, Plan
from .utils import is_valid_key
from .findstocks import find_stock

# Create your views here.


class FindStocks(APIView):
    def get(self, request, format=None):
        print(request.headers)
        if 'API-Key' in request.headers and 'Stock' in request.headers:
            valid, user_obj = is_valid_key(request.headers['API-Key'])
            if valid:
                if user_obj.has_call:
                    stock_response = find_stock(
                        request.headers['Stock'], user_obj)
                    if "Error" in stock_response.keys():
                        return Response(stock_response, status=status.HTTP_400_BAD_REQUEST)
                    return Response(stock_response, status=status.HTTP_200_OK)
                else:
                    return Response({'Error': 'Call exceeded'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'Error': 'Key invalid'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'Error': 'Key or Stock Symbol not included'}, status=status.HTTP_400_BAD_REQUEST)
