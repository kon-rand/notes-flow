class LLMError(Exception):
    """Базовое исключение для ошибок LLM"""
    pass


class LLMTimeoutError(LLMError):
    """Таймаут запроса к LLM"""
    pass


class LLMNetworkError(LLMError):
    """Сетевая ошибка при обращении к LLM"""
    pass


class LLMResponseError(LLMError):
    """Ошибка ответа от LLM (неверный формат, HTTP ошибки)"""
    pass