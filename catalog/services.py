from .models import Category, Brand, Product, ProductImage
from django.db import transaction
from django.db.models import QuerySet

class CategoryService:
    @staticmethod
    def get_categories() -> QuerySet:
        return Category.objects.filter(is_active=True).prefetch_related('children')


# class ProductService:

#     @staticmethod
#     @transaction.atomic
#     def create_product_with_image(
#             name: str, 
#             category_id: int, 
#             brand_id: int, 
#             price: float,
#             description: str,
#             stock: int,
#             images_files: list[str],
#         ) -> Product:

#         category = Category.objects.get(id=category_id)
#         brand = Brand.objects.get(id=brand_id)

#         product = Product.objects.create(
#             name=name,
#             category=category,
#             brand=brand,
#             price=price,
#             description=description,
#             stock=stock,
#         )

#         for file in images_files:
#             ProductImage.objects.filter(product=product, image_file=file)