from collections import OrderedDict
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView

from common import RestrictStaffProductManagement, EditWithinFifteenMinutes, IsModerator, CanCreateProductByAge

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ReviewSerializer,
    ProductWithReviewsSerializer,
    CategoryValidateSerializer,
    ProductValidateSerializer,
    ReviewValidateSerializer
)

PAGE_SIZE = 5

class CustomPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('total', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))

    def get_page_size(self, request):
        return PAGE_SIZE


class CategoryListCreateAPIView(ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPagination


class CategoryDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'id'


class ProductListCreateAPIView(ListCreateAPIView):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    # FIX: Stop staff members from executing POST requests here!
    permission_classes = [RestrictStaffProductManagement, CanCreateProductByAge]

    def post(self, request, *args, **kwargs):
        serializer = ProductValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Let the serializer handle validation and instantiation
        product = Product.objects.create(**serializer.validated_data)
        return Response(data=ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    lookup_field = 'id'
    # Protected globally and at the object level
    permission_classes = [RestrictStaffProductManagement & (EditWithinFifteenMinutes | IsModerator)]

    def put(self, request, *args, **kwargs):
        product = self.get_object() # 💡 This line automatically fires 'has_object_permission'!
        serializer = ProductValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Pythonic update loop dynamically assigning validated data
        for attr, value in serializer.validated_data.items():
            setattr(product, attr, value)
        product.save()

        return Response(data=ProductSerializer(product).data)


class ReviewViewSet(ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = CustomPagination
    lookup_field = 'id'


class ProductWithReviewsAPIView(APIView):
    def get(self, request):
        paginator = CustomPagination()
        products = Product.objects.select_related('category').prefetch_related('reviews').all()
        result_page = paginator.paginate_queryset(products, request)

        serializer = ProductWithReviewsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)