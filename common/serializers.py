from rest_framework import serializers

class IdModelSerializer(serializers.ModelSerializer):
    """
    Serializer with id included in the field
    """
    def get_field_names(self, declared_fields, info):
        fields=super(IdModelSerializer,self).get_field_names(declared_fields,info=info)
        fields.append('id')
        fields.append('created_on')
        fields.append('last_updated_on')
        return fields