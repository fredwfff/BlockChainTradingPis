# The Consensus class is responsible for ensuring that blocks in the blockchain are valid and
# properly signed. It is a key part of maintaining the integrity of the blockchain. In this class,
# blocks are signed by a trusted entity (the ledger manager), and validators check the signature 
# to verify the authenticity of the block.

# Key functionalities:
# 1. **sign_block**: Signs the block header using the private key. This ensures that the block
#    is legitimate and authorised by the ledger manager.
# 2. **validate_block**: Verifies the signature of a block by comparing it with the ledger manager's 
#    public key. If the block is valid, it confirms that the block has not been tampered with.

# Blockchain signatures:
# - **Who signs**: The ledger manager (or another trusted entity) signs the block with its private key. 
#   This proves that the block is part of the legitimate blockchain and has not been altered.
# - **Who validates**: Validators (network participants) verify the block by checking the signature 
#   against the ledger manager's public key to ensure the block's authenticity.

class Consensus:
    def __init__(self, security, logger):
        self.security = security
        self.logger = logger

    def sign_block(self, block):
        block_header_str = self.security.transaction_to_string(block['header'])
        signature = self.security.sign_data(block_header_str)
        block['header']['ledger_manager_signature'] = signature
        return block

    def validate_block(self, block):
        public_key_pem = self.security.get_public_key_pem()
        block_header_copy = block['header'].copy()
        signature = block_header_copy.pop('ledger_manager_signature', '')
        block_header_str = self.security.transaction_to_string(block_header_copy)
        return self.security.verify_signature(block_header_str, signature, public_key_pem)
