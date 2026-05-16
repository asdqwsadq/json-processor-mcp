import sys, json, asyncio
sys.path.insert(0, __import__('os').path.dirname(__file__))
from server import main
asyncio.run(main())
