"""领域基础异常。

定义所有领域异常的基类。
"""


class DomainException(Exception):
    """领域异常基类。

    所有领域层的异常都应该继承此类。
    """

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        """初始化领域异常。

        Args:
            message: 异常消息
            code: 异常代码
        """
        self.message = message
        self.code = code
        super().__init__(self.message)
