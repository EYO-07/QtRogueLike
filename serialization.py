# serialization.py 

# WARNING !!! This class could cause infinite recursion !!! 

# A.I. ChatGPT assisted !

# DSL Logic [ Serializable Class ]
# vS := Member Variables
# mS := Member Methods 
# 1. Serializable {}? || vS | mS
# -> vS || $ (string) class_name | $ (set) _ignored_keys 
# 2. mS || toData() | fromData() | Save_JSON() | Load_JSON() | _serialize() | _deserialize() | (static method) _get_class_by_name()
# -> mS || toData() || Returns a Serialized Dictionary of self 
# -> mS || ... | fromData(dictionary) || Reconstruct a Object from Serialized Dictionary
# -> mS || ... | Save_JSON(filename) || Save a Serialized Dictionary of Self in JSON format 
# -> mS || ... | Load_JSON(filename) || Load a JSON file | Reconstruct a Object from Serialized JSON file 
# -> mS || ... | _serialize(value) || Helper Function to Address Nested, Listed or Dicted values
# -> mS || ... | _deserialize(value,target) || Helper Function to Address Nested Complex Objects 
# -> mS || ... | _get_class_by_name(name) || Helper Function to Create a Object by name 

from pathlib import Path
import tempfile, shutil, os, json
import threading
from collections import defaultdict
            
class Serializable:
    _registry = {}
    _registry_lock = threading.Lock()
    _file_locks = defaultdict(threading.Lock)
    
    def __init__(self):
        self.class_name = self.__class__.__name__  # Auto-assign based on class
        # Use class-declared serialization preferences if available
        if hasattr(self.__class__, "__serialize_only__"):
            self._explicit_keys = set(self.__class__.__serialize_only__)
            self._ignored_keys = set()
        else:
            self._ignored_keys = {"_ignored_keys", "class_name"}
            if hasattr(self.__class__, "__ignore_serialize__"):
                self._ignored_keys |= set(self.__class__.__ignore_serialize__)
        
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__serialize_only__") and hasattr(cls, "__ignore_serialize__"):
            raise ValueError(
                f"{cls.__name__} cannot define both __serialize_only__ and __ignore_serialize__."
            )
        with Serializable._registry_lock:
            Serializable._registry[cls.__name__] = cls
    
    def to_dict(self):
        data = {"class_name": self.class_name}
        
        keys_to_serialize = getattr(self, "_explicit_keys", None)
        if keys_to_serialize is None:
            keys_to_serialize = (k for k in self.__dict__.keys() if k not in self._ignored_keys)

        for key in keys_to_serialize:
            value = self.__dict__[key]
            if isinstance(value, Serializable):
                data[key] = value.to_dict()
            else:
                data[key] = self._serialize(value)
        return data
    
    def from_dict(self, dictionary):
        if dictionary.get("class_name") != self.class_name:
            print(f"Warning: class mismatch ({dictionary.get('class_name')} != {self.class_name})")
            return False
        for key, value in dictionary.items():
            if key in self._ignored_keys or key == "class_name":
                continue
            current_attr = getattr(self, key, None)
            deserialized_value = self._deserialize(value, current_attr)
            setattr(self, key, deserialized_value)
        return True
    
    def Save_JSON(self, filename):
        filename = Path(filename)
        temp_name = None  # ensure it's defined for cleanup
        
        file_lock = Serializable._file_locks[str(filename)]
        
        with file_lock:
            try:
                with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', dir=filename.parent) as tmp_file:
                    json.dump(self.to_dict(), tmp_file, indent=4)
                    temp_name = tmp_file.name
                shutil.move(temp_name, filename)  # atomic replace
                return True
            except Exception as e:
                print(f"Error saving JSON to {filename}: {e}")
                if temp_name and os.path.exists(temp_name):
                    try:
                        os.remove(temp_name)
                    except Exception as cleanup_err:
                        print(f"Warning: failed to clean up temp file {temp_name}: {cleanup_err}")
                return False
    
    def Load_JSON(self, filename):
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return False
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.from_dict(data)
        except Exception as e:
            print(f"Error loading JSON from {filename}: {e}")
            return False
    
    def _serialize(self, value):
        if isinstance(value, Serializable):
            return value.to_dict()
        elif isinstance(value, tuple):
            return {"__tuple__": [self._serialize(v) for v in value]}
        elif isinstance(value, set):
            return {"__set__": [self._serialize(v) for v in value]}
        elif isinstance(value, frozenset):
            return {"__frozenset__": [self._serialize(v) for v in value]}
        elif isinstance(value, list):
            return [self._serialize(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}
        else:
            return value
        
    def _deserialize(self, value, target):
        if isinstance(value, dict):
            if "__tuple__" in value:
                return tuple(self._deserialize(v, None) for v in value["__tuple__"])
            elif "__set__" in value:
                return set(self._deserialize(v, None) for v in value["__set__"])
            elif "__frozenset__" in value:
                return frozenset(self._deserialize(v, None) for v in value["__frozenset__"])
            elif "class_name" in value:
                if isinstance(target, Serializable):
                    target.from_dict(value)
                    return target
                else:
                    cls_name = value.get("class_name")
                    cls = self._get_class_by_name(cls_name)
                    if cls:
                        obj = cls()
                        obj.from_dict(value)
                        return obj
                    else:
                        print(f"Warning: Unknown class '{cls_name}' during deserialization.")
                        return value
            else:
                return {k: self._deserialize(v, None) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize(v, None) for v in value]
        else:
            return value

    def set_ignored_keys(self, keys):
        """Explicitly set ignored keys for serialization"""
        self._ignored_keys = set(keys) | {"_ignored_keys", "class_name"}

    def append_ignored_keys(self, *keys):
        """Append one or more keys to the ignored list"""
        self._ignored_keys.update(keys)

    def set_serialized_keys(self, keys):
        """Switch from 'ignore mode' to 'explicit allow list'"""
        self._explicit_keys = set(keys)
        self._ignored_keys = set()  # optional: prevent mixing

    def get_ignored_keys(self):
        return iter(self._ignored_keys)

    def get_serialized_keys(self):
        if hasattr(self, "_explicit_keys"):
            return iter(self._explicit_keys)
        else:
            return (k for k in self.__dict__.keys() if k not in self._ignored_keys)

    # def __repr__(self):
        # return f"<{self.__class__.__name__} {self.to_dict()}>"

    @staticmethod
    def _get_class_by_name(name):
        return Serializable._registry.get(name, None)