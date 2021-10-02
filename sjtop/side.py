from dataclasses import dataclass
from typing import Optional
import rich
from shioaji.constant import SecurityType

from shioaji.contracts import Contract, Contracts
from textual.message import Message
from textual._types import MessageTarget
from textual.widgets import TreeControl, TreeNode, TreeClick
from textual.reactive import Reactive
from textual.events import Mount


@dataclass
class ContractEntry:
    code: Optional[str]
    security_type: Optional[SecurityType]
    exchange: Optional[str]
    is_contracts: bool


@rich.repr.auto
class ContractClick(Message, bubble=True):
    def __init__(self, sender: MessageTarget, contract: Contract) -> None:
        self.contract = contract
        super().__init__(sender)


class ContractsTree(TreeControl[ContractEntry]):
    def __init__(self, contracts: Contracts, name: str = None) -> None:
        self.contract: Optional[Contract] = None
        self.contracts = contracts
        label = "Contracts"
        data = ContractEntry(
            label, security_type=None, exchange=None, is_contracts=True
        )
        super().__init__(label, name=name, data=data)
        self.root.tree.guide_style = "black"

    has_focus: Reactive[bool] = Reactive(False)

    def on_focus(self) -> None:
        self.has_focus = True

    def on_blur(self) -> None:
        self.has_focus = False

    async def on_mount(self, event: Mount) -> None:
        await self.load_contracts(self.root)

    async def load_contracts(self, node: TreeNode[ContractEntry]):
        if not node.data.security_type:
            for secu_type, cstream in self.contracts:
                await node.add(
                    secu_type,
                    ContractEntry(
                        code=None,
                        security_type=getattr(SecurityType, secu_type[:-1]),
                        exchange=None,
                        is_contracts=True,
                    ),
                )
        else:
            cstream = getattr(self.contracts, f"{node.data.security_type.name}s")
            if not node.data.exchange:
                for cs in cstream:
                    await node.add(
                        cs._name,
                        ContractEntry(
                            code=None,
                            security_type=node.data.security_type,
                            exchange=cs._name,
                            is_contracts=True,
                        ),
                    )
            else:
                cs = getattr(cstream, node.data.exchange)
                cs_sorted = sorted([c for c in cs], key=lambda x: x.code)
                for c in cs_sorted:
                    if node.data.security_type == SecurityType.Stock:
                        if len(c.code) == 4:
                            await node.add(
                                c.code,
                                ContractEntry(
                                    code=c.code,
                                    security_type=node.data.security_type,
                                    exchange=cs._name,
                                    is_contracts=False,
                                ),
                            )
                    else:
                        await node.add(
                            c.code,
                            ContractEntry(
                                code=c.code,
                                security_type=node.data.security_type,
                                exchange=cs._name,
                                is_contracts=False,
                            ),
                        )

        node.loaded = True
        await node.expand()
        self.refresh(layout=True)

    async def handle_tree_click(self, message: TreeClick[ContractEntry]) -> None:
        contract_entry = message.node.data
        if not contract_entry.is_contracts:
            contract = getattr(self.contracts, f"{contract_entry.security_type.name}s")[
                contract_entry.code
            ]
            await self.emit(ContractClick(self, contract))
        else:
            if not message.node.loaded:
                await self.load_contracts(message.node)
                await message.node.expand()
            else:
                await message.node.toggle()
