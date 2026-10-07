"""Test script to verify USD (Universal Scene Description) is properly installed."""
from pxr import Usd
print("USD import successful")
print("USD version:", Usd.GetVersion())
