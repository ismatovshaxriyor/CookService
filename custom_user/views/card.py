from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from custom_user.models import Card
from custom_user.pagination import CustomPageNumberPagination
from custom_user.serializers import CardSerializer, CardCreateSerializer, CardUpdateSerializer, ErrorResponseSerializer


class CardListView(APIView):
    """User'ning barcha kartalari (paginated, default birinchi)"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name='page', description='Sahifa raqami', required=False, type=int),
            OpenApiParameter(name='page_size', description='Sahifadagi elementlar soni', required=False, type=int),
        ],
        responses={
            200: OpenApiResponse(
                response=CardSerializer(many=True),
                description='Kartalar ro\'yxati'
            ),
        },
        tags=['Cards'],
        summary='Kartalar ro\'yxati',
        description='User\'ning barcha kartalari (default birinchi, pagination bilan)',
        operation_id='cards_list',
    )
    def get(self, request):
        cards = Card.objects.filter(user=request.user)

        # Pagination
        paginator = self.pagination_class()
        paginated_cards = paginator.paginate_queryset(cards, request)

        serializer = CardSerializer(paginated_cards, many=True)

        return paginator.get_paginated_response(serializer.data)


class CardCreateView(APIView):
    """Yangi karta qo'shish"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CardCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=CardSerializer,
                description='Karta muvaffaqiyatli yaratildi'
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Validatsiya xatosi'
            ),
        },
        tags=['Cards'],
        summary='Yangi karta qo\'shish',
        description='User uchun yangi karta yaratish'
    )
    def post(self, request):
        serializer = CardCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        card = serializer.save(user=request.user)

        return Response({
            'success': True,
            'message': 'Karta muvaffaqiyatli qo\'shildi',
            'card': CardSerializer(card).data
        }, status=status.HTTP_201_CREATED)


class CardDetailView(APIView):
    """Bitta kartani ko'rish, yangilash, o'chirish"""
    permission_classes = [IsAuthenticated]

    def get_object(self, uid):
        try:
            return Card.objects.get(uid=uid, user=self.request.user)
        except Card.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: CardSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Cards'],
        summary='Kartani ko\'rish',
        operation_id='card_retrieve_details',
    )
    def get(self, request, uid):
        card = self.get_object(uid)

        if not card:
            return Response(
                {'error': 'Karta topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'success': True,
            'card': CardSerializer(card).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        request=CardUpdateSerializer,
        responses={
            200: CardSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Cards'],
        summary='Kartani yangilash',
        description='Partial update - faqat yuborilgan fieldlar yangilanadi'
    )
    def patch(self, request, uid):
        card = self.get_object(uid)

        if not card:
            return Response(
                {'error': 'Karta topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CardUpdateSerializer(card, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response({
            'success': True,
            'message': 'Karta yangilandi',
            'card': CardSerializer(card).data
        }, status=status.HTTP_200_OK)

    @extend_schema(
        responses={
            200: OpenApiResponse(description='Karta o\'chirildi'),
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Cards'],
        summary='Kartani o\'chirish',
    )
    def delete(self, request, uid):
        card = self.get_object(uid)

        if not card:
            return Response(
                {'error': 'Karta topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Agar default karta o'chirilsa
        was_default = card.default
        card.delete()

        # Keyingi kartani default qilish
        if was_default:
            next_card = Card.objects.filter(user=request.user).first()
            if next_card:
                next_card.default = True
                next_card.save()

        return Response({
            'success': True,
            'message': 'Karta o\'chirildi'
        }, status=status.HTTP_200_OK)


class CardSetDefaultView(APIView):
    """Kartani default qilish"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: CardSerializer,
            404: ErrorResponseSerializer,
        },
        tags=['Cards'],
        summary='Asosiy karta qilish',
        description='Tanlangan kartani default (asosiy) qilish'
    )
    def post(self, request, uid):
        try:
            card = Card.objects.get(uid=uid, user=request.user)
        except Card.DoesNotExist:
            return Response(
                {'error': 'Karta topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Default qilish
        card.default = True
        card.save()

        return Response({
            'success': True,
            'message': 'Asosiy karta o\'zgartirildi',
            'card': CardSerializer(card).data
        }, status=status.HTTP_200_OK)