def serializer_error_to_dict(error):
    return {key: [str(error) for error in error[key]] for key in error.keys()}
