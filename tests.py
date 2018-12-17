from django.test import TestCase

from .singularity import *

# Create your tests here.
class SingularityTest(TestCase):
    def setUp(self):
        self.path = "/home/test/singularity-images/output"

    def test_containers(self):
        containers = get_all_container(self.path)
        self.assertEqual(len(containers), 1, 'Yo')
        mapped = [get_container_details(x) for x in containers]
        print(mapped)
        print(containers)
