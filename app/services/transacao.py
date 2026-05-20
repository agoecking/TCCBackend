import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

CONTRACT_ADDRESS = "0x8757cde93797e8cE0543e2fCa23714D231d9c86D"

# ABI mínima com as funções usadas pelo backend
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "eventId", "type": "uint256"},
            {"internalType": "string",  "name": "tokenURI", "type": "string"}
        ],
        "name": "mintTicket",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "price",   "type": "uint256"}
        ],
        "name": "listForResale",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "buyResaleTicket",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "cancelResaleListing",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "eventId", "type": "uint256"}],
        "name": "getEventInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "string",  "name": "name",           "type": "string"},
                    {"internalType": "uint256", "name": "ticketPrice",    "type": "uint256"},
                    {"internalType": "uint256", "name": "maxTickets",     "type": "uint256"},
                    {"internalType": "uint256", "name": "soldTickets",    "type": "uint256"},
                    {"internalType": "uint256", "name": "maxResalePrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "royaltyBps",     "type": "uint256"},
                    {"internalType": "address", "name": "organizer",      "type": "address"},
                    {"internalType": "bool",    "name": "active",         "type": "bool"}
                ],
                "internalType": "struct KoynTicket.Event",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "isTicketValid",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "resaleListings",
        "outputs": [
            {"internalType": "address", "name": "seller", "type": "address"},
            {"internalType": "uint256", "name": "price",  "type": "uint256"},
            {"internalType": "bool",    "name": "active", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string",  "name": "name",           "type": "string"},
            {"internalType": "uint256", "name": "ticketPrice",    "type": "uint256"},
            {"internalType": "uint256", "name": "maxTickets",     "type": "uint256"},
            {"internalType": "uint256", "name": "maxResalePrice", "type": "uint256"},
            {"internalType": "uint256", "name": "royaltyBps",     "type": "uint256"}
        ],
        "name": "createEvent",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "internalType": "uint256", "name": "eventId",   "type": "uint256"},
            {"indexed": False, "internalType": "string",  "name": "name",      "type": "string"},
            {"indexed": False, "internalType": "address", "name": "organizer", "type": "address"}
        ],
        "name": "EventCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "internalType": "uint256", "name": "tokenId",  "type": "uint256"},
            {"indexed": True,  "internalType": "uint256", "name": "eventId",  "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "buyer",    "type": "address"}
        ],
        "name": "TicketMinted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": False, "internalType": "address", "name": "from",    "type": "address"},
            {"indexed": False, "internalType": "address", "name": "to",      "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "price",   "type": "uint256"}
        ],
        "name": "TicketSold",
        "type": "event"
    }
]


class BlockchainService:
    """Gerencia a conexão com o contrato KoynTicket na Sepolia."""

    def __init__(self):
        rpc_url     = os.getenv("ALCHEMY_RPC_URL")
        private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

        if not rpc_url or not private_key:
            raise EnvironmentError(
                "ALCHEMY_RPC_URL e BLOCKCHAIN_PRIVATE_KEY são obrigatórios no .env"
            )

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Não foi possível conectar ao nó Sepolia via Alchemy")

        self.account = self.w3.eth.account.from_key(private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI,
        )

    def _send_transaction(self, fn, value_wei: int = 0) -> object:
        """Constrói, assina e envia uma transação. Aguarda o recibo."""
        nonce     = self.w3.eth.get_transaction_count(self.account.address)
        gas_price = self.w3.eth.gas_price

        tx = fn.build_transaction({
            "from":     self.account.address,
            "value":    value_wei,
            "nonce":    nonce,
            "gasPrice": gas_price,
        })
        tx["gas"] = self.w3.eth.estimate_gas(tx)

        signed  = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt.status != 1:
            raise Exception(f"Transação revertida. Hash: {tx_hash.hex()}")

        return receipt

    # ── Funções de escrita ────────────────────────────────────────────────────

    def create_event(self, name: str, ticket_price_wei: int, max_tickets: int,
                     max_resale_price_wei: int, royalty_bps: int) -> int:
        """
        Chama createEvent() no contrato e retorna o blockchain_event_id.

        Args:
            name:                Nome do evento
            ticket_price_wei:    Preço por ingresso em wei
            max_tickets:         Capacidade máxima
            max_resale_price_wei: Teto de revenda em wei (0 = sem limite)
            royalty_bps:         Royalty do organizador em basis points (1000 = 10%)

        Returns:
            blockchain_event_id (int)
        """
        fn      = self.contract.functions.createEvent(
            name, ticket_price_wei, max_tickets, max_resale_price_wei, royalty_bps
        )
        receipt = self._send_transaction(fn)

        logs     = self.contract.events.EventCreated().process_receipt(receipt)
        event_id = logs[0]["args"]["eventId"] if logs else None
        return event_id

    def mint_ticket(self, blockchain_event_id: int, token_uri: str) -> dict:
        """
        Chama mintTicket() no contrato.

        O NFT é mintado para a carteira administradora do backend.
        O token_id e tx_hash são salvos no banco pelo IngressoService.

        Retorna: {"token_id": int, "tx_hash": str}
        """
        event_info     = self.contract.functions.getEventInfo(blockchain_event_id).call()
        ticket_price   = event_info[1]  # ticketPrice em wei

        fn      = self.contract.functions.mintTicket(blockchain_event_id, token_uri)
        receipt = self._send_transaction(fn, value_wei=ticket_price)

        logs     = self.contract.events.TicketMinted().process_receipt(receipt)
        token_id = logs[0]["args"]["tokenId"] if logs else None

        return {
            "token_id": token_id,
            "tx_hash":  receipt.transactionHash.hex(),
        }

    def list_for_resale(self, token_id: int, price_wei: int) -> str:
        """Coloca um ingresso à venda no mercado de revenda. Retorna tx_hash."""
        fn      = self.contract.functions.listForResale(token_id, price_wei)
        receipt = self._send_transaction(fn)
        return receipt.transactionHash.hex()

    def cancel_resale_listing(self, token_id: int) -> str:
        """Cancela a listagem de revenda. Retorna tx_hash."""
        fn      = self.contract.functions.cancelResaleListing(token_id)
        receipt = self._send_transaction(fn)
        return receipt.transactionHash.hex()

    def buy_resale_ticket(self, token_id: int) -> str:
        """Compra um ingresso no mercado de revenda. Retorna tx_hash."""
        listing   = self.contract.functions.resaleListings(token_id).call()
        price_wei = listing[1]

        fn      = self.contract.functions.buyResaleTicket(token_id)
        receipt = self._send_transaction(fn, value_wei=price_wei)
        return receipt.transactionHash.hex()

    # ── Funções de leitura (view) ─────────────────────────────────────────────

    def get_event_info(self, blockchain_event_id: int) -> dict:
        """Busca informações de um evento diretamente no contrato."""
        info = self.contract.functions.getEventInfo(blockchain_event_id).call()
        return {
            "name":               info[0],
            "ticket_price_wei":   info[1],
            "max_tickets":        info[2],
            "sold_tickets":       info[3],
            "max_resale_price_wei": info[4],
            "royalty_bps":        info[5],
            "organizer":          info[6],
            "active":             info[7],
        }

    def get_ticket_owner(self, token_id: int) -> str:
        """Retorna o endereço Ethereum dono do NFT."""
        return self.contract.functions.ownerOf(token_id).call()

    def is_ticket_valid(self, token_id: int) -> bool:
        """Verifica se o NFT existe e é válido no contrato."""
        return self.contract.functions.isTicketValid(token_id).call()

    def get_resale_listing(self, token_id: int) -> dict:
        """Retorna dados de uma listagem de revenda."""
        listing = self.contract.functions.resaleListings(token_id).call()
        return {
            "seller": listing[0],
            "price_wei": listing[1],
            "active": listing[2],
        }


class TransacaoService:
    """
    Fachada de alto nível para operações blockchain do Koyn.
    Usado pelo IngressoService para mint e revenda de ingressos.
    """

    def __init__(self):
        self.blockchain = BlockchainService()

    def criar_evento_blockchain(self, nome: str, ticket_price_wei: int, max_tickets: int,
                                max_resale_price_wei: int = 0, royalty_bps: int = 1000) -> int:
        """
        Cria o evento no contrato KoynTicket.

        Args:
            nome:                 Nome do evento
            ticket_price_wei:     Preço por ingresso em wei
            max_tickets:          Capacidade máxima
            max_resale_price_wei: Teto de revenda em wei (0 = sem limite)
            royalty_bps:          Royalty em basis points (padrão: 1000 = 10%)

        Returns:
            blockchain_event_id (int)
        """
        return self.blockchain.create_event(
            nome, ticket_price_wei, max_tickets, max_resale_price_wei, royalty_bps
        )

    def mint_nft(self, blockchain_event_id: int, token_uri: str = "") -> dict:
        """
        Minta um NFT para o evento informado.

        Args:
            blockchain_event_id: ID do evento no contrato KoynTicket
            token_uri: URI dos metadados do ingresso (pode ser vazio em dev)

        Returns:
            {"token_id": int, "tx_hash": str}
        """
        return self.blockchain.mint_ticket(blockchain_event_id, token_uri)

    def anunciar_revenda(self, token_id: int, price_wei: int) -> str:
        """
        Coloca o ingresso à venda no contrato.

        Args:
            token_id:  ID do NFT
            price_wei: Preço de revenda em wei

        Returns:
            tx_hash da transação
        """
        return self.blockchain.list_for_resale(token_id, price_wei)

    def cancelar_revenda(self, token_id: int) -> str:
        """Cancela a listagem de revenda no contrato. Retorna tx_hash."""
        return self.blockchain.cancel_resale_listing(token_id)

    def comprar_revenda(self, token_id: int) -> str:
        """
        Compra um ingresso no mercado de revenda.

        Returns:
            tx_hash da transação
        """
        return self.blockchain.buy_resale_ticket(token_id)

    def validar_ingresso(self, token_id: int) -> bool:
        """Verifica se o NFT existe e é válido no contrato."""
        return self.blockchain.is_ticket_valid(token_id)

    def info_evento_blockchain(self, blockchain_event_id: int) -> dict:
        """Retorna dados do evento diretamente do contrato."""
        return self.blockchain.get_event_info(blockchain_event_id)
