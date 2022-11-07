from operator import length_hint
from cards import generate_deck
import numpy as np
from typing import List, Dict
import math
from pearhash import PearsonHasher
from enum import Enum
from dahuffman import HuffmanCodec
from collections import namedtuple


class Domain(Enum):
    ALL = 0
    NUM = 1
    LOWER = 2
    LOWER_AND_UPPER = 3
    LETTERS_NUMBERS = 4
    LAT_LONG = 5

MAX_DOMAIN_VALUE = max([d.value for d in Domain])

DomainFrequencies = {
    # reference of English letter frequencies: https://pi.math.cornell.edu/~mec/2003-2004/cryptography/subs/frequencies.html
    Domain.ALL: {"a": 8.12, "b": 1.49, "c": 2.71, "d": 4.32, "e": 12.02, "f": 2.30, "g": 2.03, "h": 5.92, "i": 7.31, "j": 0.10, "k": 0.69, "l": 3.98, "m": 2.61, "n": 6.95, "o": 7.68, "p": 1.82, "q": 0.11, "r": 6.02, "s": 6.28, "t": 9.10, "u": 2.88, "v": 1.11, "w": 2.09, "x": 0.17, "y": 2.11, "z": 0.07, " ": 0.11, "\t": 0.10, ".": 6.97, ",": 5.93, "'": 1.53, "\"": 1.33, ":": 0.90, "-": 0.77, ";": 0.74, "?": 0.43, "!": 0.39, "0": 0.09, "1": 0.08, "2": 0.07, "3": 0.06, "4": 0.05, "5": 0.04, "6": 0.03, "7": 0.02, "8": 0.01, "9": 0.005},
    Domain.LAT_LONG: {"0": 186, "1": 342, "2": 223, "3": 334, "4": 208, "5": 215, "6": 233, "7": 211, "8": 173, "9": 168, "N": 169, "E": 164, "S": 31, "W": 36, ",": 200, ".": 400, " ": 600},
    Domain.LOWER: {"a": 8.12, "b": 1.49, "c": 2.71, "d": 4.32, "e": 12.02, "f": 2.30, "g": 2.03, "h": 5.92, "i": 7.31, "j": 0.10, "k": 0.69, "l": 3.98, "m": 2.61, "n": 6.95, "o": 7.68, "p": 1.82, "q": 0.11, "r": 6.02, "s": 6.28, "t": 9.10, "u": 2.88, "v": 1.11, "w": 2.09, "x": 0.17, "y": 2.11, "z": 0.07},
    Domain.LOWER_AND_UPPER: {"a": 8.12, "b": 1.49, "c": 2.71, "d": 4.32, "e": 12.02, "f": 2.30, "g": 2.03, "h": 5.92, "i": 7.31, "j": 0.10, "k": 0.69, "l": 3.98, "m": 2.61, "n": 6.95, "o": 7.68, "p": 1.82, "q": 0.11, "r": 6.02, "s": 6.28, "t": 9.10, "u": 2.88, "v": 1.11, "w": 2.09, "x": 0.17, "y": 2.11, "z": 0.07, "A": 0.812, "B": 0.149, "C": 0.271, "D": 0.432, "E": 1.202, "F": 0.230, "G": 0.203, "H": 0.592, "I": 0.731, "J": 0.01, "K": 0.069, "L": 0.398, "M": 0.261, "N": 0.695, "O": 0.768, "P": 0.182, "Q": 0.011, "R": 0.602, "S": 0.628, "T": 0.91, "U": 0.288, "V": 0.111, "W": 0.209, "X": 0.017, "Y": 0.211, "Z": 0.007},
    Domain.LETTERS_NUMBERS: {"a": 8.12, "b": 1.49, "c": 2.71, "d": 4.32, "e": 12.02, "f": 2.30, "g": 2.03, "h": 5.92, "i": 7.31, "j": 0.10, "k": 0.69, "l": 3.98, "m": 2.61, "n": 6.95, "o": 7.68, "p": 1.82, "q": 0.11, "r": 6.02, "s": 6.28, "t": 9.10, "u": 2.88, "v": 1.11, "w": 2.09, "x": 0.17, "y": 2.11, "z": 0.07, "A": 0.812, "B": 0.149, "C": 0.271, "D": 0.432, "E": 1.202, "F": 0.230, "G": 0.203, "H": 0.592, "I": 0.731, "J": 0.01, "K": 0.069, "L": 0.398, "M": 0.261, "N": 0.695, "O": 0.768, "P": 0.182, "Q": 0.011, "R": 0.602, "S": 0.628, "T": 0.91, "U": 0.288, "V": 0.111, "W": 0.209, "X": 0.017, "Y": 0.211, "Z": 0.007, "0": 0.09, "1": 0.08, "2": 0.07, "3": 0.06, "4": 0.05, "5": 0.04, "6": 0.03, "7": 0.02, "8": 0.01, "9": 0.005},
    Domain.NUM: {"0": 0.09, "1": 0.08, "2": 0.07, "3": 0.06, "4": 0.05, "5": 0.04, "6": 0.03, "7": 0.02, "8": 0.01, "9": 0.005},
}

EncodedBinary = namedtuple(
    'EncodedBinary', ['message_bits', 'checksum_bits'])


class Agent:
    def __init__(self):
        self.rng = np.random.default_rng(seed=42)
        self.hash = None

    def string_to_binary(self, message: str, domain: Domain) -> str:
        bytes_repr = HuffmanCodec.from_frequencies(
            self.get_domain_frequencies(domain)).encode(message)
        binary_repr = bin(int(bytes_repr.hex(), 16))[2:]
        return binary_repr

    def binary_to_string(self, binary: str, domain: Domain) -> str:
        message_byte = int(binary, 2).to_bytes(
            (int(binary, 2).bit_length() + 7) // 8, 'big')
        message = HuffmanCodec.from_frequencies(
            self.get_domain_frequencies(domain)).decode(message_byte)
        return message

    def deck_encoded(self, message_cards: List[int]) -> List[int]:
        result = []
        for i in range(52):
            if i not in message_cards:
                result.append(i)
        result.extend(message_cards)
        return result

    def get_encoded_cards(self, deck: List[int], start_card_num: int, end_card_num=51) -> List[int]:
        return [c for c in reversed(deck) if c >= start_card_num and c <= end_card_num]

    def cards_to_num(self, cards: List[int]) -> int:
        num_cards = len(cards)

        if num_cards == 1:
            return 0

        ordered_cards = sorted(cards)
        sub_list_size = math.factorial(num_cards - 1)
        sub_list_indx = sub_list_size * ordered_cards.index(cards[0])

        return sub_list_indx + self.cards_to_num(cards[1:])

    def num_to_cards(self, num: int, cards: List[int]) -> List[int]:
        num_cards = len(cards)

        if num_cards == 1:
            return cards

        ordered_cards = sorted(cards)
        permutations = math.factorial(num_cards)
        sub_list_size = math.factorial(num_cards - 1)
        sub_list_indx = math.floor(num / sub_list_size)
        sub_list_start = sub_list_indx * sub_list_size

        if sub_list_start >= permutations:
            raise Exception('Number too large to encode in cards.')

        first_card = ordered_cards[sub_list_indx]
        ordered_cards.remove(first_card)

        return [first_card, *self.num_to_cards(num - sub_list_start, ordered_cards)]

    def get_hash(self, bit_string: str) -> str:
        hasher = PearsonHasher(1)
        hex_hash = hasher.hash(str(int(bit_string, 2)).encode()).hexdigest()
        return bin(int(hex_hash, 16))[2:].zfill(8)

    def domain_to_binary(self, domain_type: Domain) -> str:
        return bin(int(domain_type.value))[2:].zfill(3)

    def get_domain_type(self, message: str) -> Domain:
        clean_message = "".join(message.split())
        if clean_message.isnumeric():
            return Domain.NUM
        elif clean_message.isalpha() and clean_message.islower():
            return Domain.LOWER
        elif clean_message.isalpha():
            return Domain.LOWER_AND_UPPER
        elif clean_message.isalnum():
            return Domain.LETTERS_NUMBERS
        elif self.is_lat_long(clean_message):
            return Domain.LAT_LONG
        else:
            return Domain.ALL

    def get_domain_frequencies(self, domain: Domain) -> Dict[Domain, Dict[str, float]]:
        return DomainFrequencies[domain] if domain in DomainFrequencies.keys() else DomainFrequencies[Domain.ALL]

    def is_lat_long(self, message: str) -> bool:
        return all([ch.isdigit() or ch in [",", ".", "N", "E", "S", "W"] for ch in message])

    def check_decoded_message(self, message: str, domain_type) -> str:
        clean_message = "".join(message.split())
        if message == '':
            return 'NULL'
        if self.get_domain_type(clean_message) == Domain.ALL:
            if not all(ord(c) < 128 and ord(c) > 32 for c in message):
                return 'NULL'
        return message

    def get_binary_parts(self, binary: str) -> EncodedBinary:
        checksum_bits = binary[-8:]
        message_bits = binary[:-8]
        return EncodedBinary(message_bits, checksum_bits)

    def encode(self, message: str) -> List[int]:
        deck = generate_deck(self.rng)

        domain_type = self.get_domain_type(message)

        binary_repr = self.string_to_binary(message, domain_type)
        self.hash = self.get_hash(binary_repr)
        
        binary_repr = binary_repr + self.get_hash(binary_repr)
        integer_repr = int(binary_repr, 2)

        num_cards_to_encode = 1
        for n in range(1, 52):
            if math.factorial(n) >= integer_repr:
                num_cards_to_encode = n
                break
        start_idx = len(deck) - num_cards_to_encode
        message_cards = self.num_to_cards(integer_repr, deck[start_idx:])
        message_cards.reverse()
        start_idx_cards = self.num_to_cards(start_idx, deck[:6])
        start_idx_cards.reverse()
        domain_cards = self.num_to_cards(domain_type.value, deck[6:9])
        domain_cards.reverse()

        return self.deck_encoded(message_cards + domain_cards + start_idx_cards)

    def decode(self, deck: List[int]) -> str:
        message = ''
        start_idx = self.cards_to_num(self.get_encoded_cards(deck, 0, 5))
        domain_int = self.cards_to_num(self.get_encoded_cards(deck, 6, 8))

        if start_idx <= 51:
            encoded_cards = self.get_encoded_cards(deck, start_idx)
            integer_repr = self.cards_to_num(encoded_cards)
            binary_repr = bin(int(integer_repr))[2:]
            parts = self.get_binary_parts(binary_repr)
            len_metadata_bits = len(parts.checksum_bits)

            if len_metadata_bits == 8 and domain_int <= MAX_DOMAIN_VALUE and parts.message_bits: # and parts.checksum_bits == self.get_hash(parts.message_bits):
                domain_type = Domain(domain_int)
                message = self.binary_to_string(parts.message_bits, domain_type)
        else:
            return 'NULL'

        return self.check_decoded_message(message, domain_type)


if __name__ == "__main__":
    agent = Agent()
    message = "Hello"
    deck = agent.encode(message)
    print(deck)
    print(agent.decode(deck))
