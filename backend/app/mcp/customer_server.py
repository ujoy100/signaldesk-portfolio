"""Read-only customer MCP server."""

from collections.abc import Callable

from mcp.server import MCPServer
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.mcp.contracts import (
    ActiveServicesOutput,
    CustomerPlanOutput,
    CustomerProfileOutput,
    ServiceStatusOutput,
)
from backend.app.models.customer import Customer
from backend.app.models.plan import Plan
from backend.app.models.subscription import Subscription


def create_customer_server(session_factory: Callable[[], Session]) -> MCPServer:
    server = MCPServer("telecom-customer", version="1.0.0")

    def customer_or_error(session: Session, customer_id: int) -> Customer:
        customer = session.get(Customer, customer_id)
        if customer is None:
            raise ValueError("customer_not_found")
        return customer

    @server.tool(structured_output=True)
    def get_customer_profile(customer_id: int) -> CustomerProfileOutput:
        """Get the fictional customer's basic profile."""

        with session_factory() as session:
            customer = customer_or_error(session, customer_id)
            return CustomerProfileOutput(
                customer_id=customer.id,
                customer_number=customer.customer_number,
                full_name=customer.full_name,
                email=customer.email,
            )

    @server.tool(structured_output=True)
    def get_customer_plan(customer_id: int) -> CustomerPlanOutput:
        """Get the customer's most recent subscription plan."""

        with session_factory() as session:
            customer_or_error(session, customer_id)
            row = session.execute(
                select(Subscription, Plan)
                .join(Plan, Plan.id == Subscription.plan_id)
                .where(Subscription.customer_id == customer_id)
                .order_by(Subscription.id.desc())
            ).first()
            if row is None:
                raise ValueError("subscription_not_found")
            subscription, plan = row
            return CustomerPlanOutput(
                customer_id=customer_id,
                plan_code=plan.plan_code,
                plan_name=plan.name,
                status=subscription.status,
            )

    @server.tool(structured_output=True)
    def check_roaming_status(customer_id: int) -> ServiceStatusOutput:
        """Report roaming eligibility from active mobile subscription facts."""

        plan = get_customer_plan(customer_id)
        eligible = plan.status == "active" and "MOBILE" in plan.plan_code.upper()
        return ServiceStatusOutput(
            customer_id=customer_id,
            service="roaming",
            status="eligible" if eligible else "not_eligible",
            basis="active mobile subscription; live roaming state is a later MCP data source",
        )

    @server.tool(structured_output=True)
    def check_data_service_status(customer_id: int) -> ServiceStatusOutput:
        """Report data service status from subscription state."""

        plan = get_customer_plan(customer_id)
        return ServiceStatusOutput(
            customer_id=customer_id,
            service="data",
            status="available" if plan.status == "active" else plan.status,
            basis="subscription status",
        )

    @server.tool(structured_output=True)
    def get_active_services(customer_id: int) -> ActiveServicesOutput:
        """List active fictional subscription services."""

        with session_factory() as session:
            customer_or_error(session, customer_id)
            rows = session.execute(
                select(Subscription, Plan)
                .join(Plan, Plan.id == Subscription.plan_id)
                .where(
                    Subscription.customer_id == customer_id,
                    Subscription.status == "active",
                )
            ).all()
            return ActiveServicesOutput(
                customer_id=customer_id,
                services=[
                    {
                        "plan_code": plan.plan_code,
                        "name": plan.name,
                        "status": sub.status,
                    }
                    for sub, plan in rows
                ],
            )

    return server
