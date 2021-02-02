from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ApiUser, Plan
from .utils import is_valid_key

# Create your views here.


class FindStocks(APIView):
    def get(self, request, format=None):
        print(request.headers)
        if 'API-Key' in request.headers:
            valid, user_obj = is_valid_key(request.headers['API-Key'])
            if valid:
                if user_obj.has_call:
                    user_obj.call_used_today += 1
                    user_obj.save(update_fields=['call_used_today'])
                    call_left = user_obj.plan.api_per_day - user_obj.call_used_today
                    return Response({"user_data": {'Call left': call_left}, "stock_data": {"pe": 123, "marketCap": 456}}, status=status.HTTP_200_OK)
                else:
                    return Response({'Error': 'Call exceeded'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'Error': 'Key invalid'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'Error': 'Key Not Included'}, status=status.HTTP_400_BAD_REQUEST)
