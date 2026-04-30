from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from .agent_controller import AgentOperationController
from .agent_controller import EmailRecipentsOperationController

# Not adding JWT Auth for Development

api_v1= NinjaExtraAPI(version="1.0.0")

api_v1.register_controllers(AgentOperationController)

api_v1.register_controllers(EmailRecipentsOperationController)