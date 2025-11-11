# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """read a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found = Product.find(product.id)
        self.assertEqual(found.id, product.id)
        self.assertEqual(found.name, product.name)
        self.assertEqual(found.description, product.description)
        self.assertEqual(found.price, product.price)
        self.assertEqual(found.available, product.available)
        self.assertEqual(found.category, product.category)
    
    def test_update_a_product(self):
        """update a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        product.description = "Change"
        root_id = product.id
        product.update()
        self.assertEqual(product.id, root_id)
        # found and check again
        found = Product.find(root_id)
        self.assertEqual(found.id, product.id)
        self.assertEqual(found.description, product.description)

    def test_delete_a_product(self):
        """delete a product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_product(self):
        """list all product"""
        products = Product.all()
        self.assertEqual(products, [])
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 10)

    def test_find_product_by_name(self):
        """find product by name"""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 10)
        search = products[0].name
        found = Product.find_by_name(search)
        for item in found:
            self.assertEqual(item.name, search)
    
    def test_find_product_by_available(self):
        """find product by available"""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 10)
        search = products[0].available
        found = Product.find_by_availability(search)
        for item in found:
            self.assertEqual(item.available, search)

    def test_find_product_by_category(self):
        """find product by category"""
        for _ in range(10):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 10)
        search = products[0].category
        found = Product.find_by_category(search)
        for item in found:
            self.assertEqual(item.category, search)
        
    def test_invalid_id_on_update(self):
        """Test invalid id update"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_invalid_type_available_on_deserialize(self):
        """Test invalid type available on deserialize"""
        data = {
            "name": "Test Product",
            "description": "invalid product",
            "price": "19.99",
            "available": "test",
            "category": Category.FOOD,
        }
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)
    
    def test_missing_field_deserialize(self):
        """Test deserialize() with missing field"""
        data = {
            "name": "Test Product",
            "description": "Missing price field",
            # thiếu 'price'
            "available": True,
            "category": "FOOD"
        }
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)
    
    def test_deserialize_bad_data_type(self):
        """Test deserialize() with no data"""
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, None)

    def test_invalid_attribute_error_on_deserialize(self):
        """Test invalid category name triggers AttributeError -> DataValidationError"""
        data = {
            "name": "Test Product",
            "description": "invalid category name",
            "price": "19.99",
            "available": True,
            "category": "INVALID_CATEGORY",  # không tồn tại trong Enum Category
        }
        product = Product()
        self.assertRaises(DataValidationError, product.deserialize, data)
    
    def test_find_product_by_price(self):
        """find product by price"""
        product = ProductFactory()
        product.price = Decimal("19.99")
        product.create()
        self.assertEqual(len(Product.all()), 1)
        found = Product.find_by_price("19.99")
        for item in found:
            self.assertEqual(item.price, product.price)
    
    

        






    
