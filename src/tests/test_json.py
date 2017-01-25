import pytest

from mashingpumpkins import json

def test():
    sketch = None
    
    with pytest.raises(NotImplementedError):
        json.validate(sketch)
        
    with pytest.raises(NotImplementedError):
        json.readsketch_iter(sketch)

    with pytest.raises(NotImplementedError):
        json.readjamschema(sketch)
