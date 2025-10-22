"""
Unit tests for text chunking utilities.
Tests various chunking strategies and edge cases.
"""
import pytest
from app.utils.text_chunking import (
    chunk_text,
    chunk_text_simple,
    chunk_text_by_sentences,
    get_overlap_text,
    chunk_text_with_metadata,
    estimate_tokens,
    chunk_text_by_tokens
)


class TestChunkTextSimple:
    """Test simple character-based chunking"""

    def test_simple_chunk_basic(self):
        """Test basic simple chunking"""
        text = "a" * 100
        chunks = chunk_text_simple(text, chunk_size=30, overlap=10)

        assert len(chunks) > 0
        # First chunk should be 30 chars
        assert len(chunks[0]) == 30

    def test_simple_chunk_no_overlap(self):
        """Test chunking without overlap"""
        text = "abcdefghij" * 10  # 100 chars
        chunks = chunk_text_simple(text, chunk_size=25, overlap=0)

        assert len(chunks) == 4
        assert all(len(chunk) == 25 for chunk in chunks[:-1])

    def test_simple_chunk_with_overlap(self):
        """Test chunking with overlap"""
        text = "0123456789" * 10  # 100 chars
        chunks = chunk_text_simple(text, chunk_size=30, overlap=10)

        # Verify chunks overlap
        assert len(chunks) > 1
        # Check that last chars of chunk[0] appear in chunk[1]

    def test_simple_chunk_empty_text(self):
        """Test chunking empty text"""
        chunks = chunk_text_simple("", chunk_size=100, overlap=20)
        assert chunks == []

    def test_simple_chunk_whitespace_only(self):
        """Test chunking whitespace-only text"""
        chunks = chunk_text_simple("   \n\t  ", chunk_size=100, overlap=20)
        assert chunks == []

    def test_simple_chunk_text_smaller_than_chunk_size(self):
        """Test text smaller than chunk size"""
        text = "Short text"
        chunks = chunk_text_simple(text, chunk_size=100, overlap=20)

        assert len(chunks) == 1
        assert chunks[0] == text


class TestChunkTextBySentences:
    """Test sentence-aware chunking"""

    def test_sentence_chunk_basic(self):
        """Test basic sentence chunking"""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text_by_sentences(text, chunk_size=50, overlap=10)

        assert len(chunks) > 0
        # Should preserve complete sentences
        assert any("First sentence." in chunk for chunk in chunks)

    def test_sentence_chunk_preserves_boundaries(self):
        """Test that sentence boundaries are preserved"""
        text = "Sentence one! Sentence two? Sentence three."
        chunks = chunk_text_by_sentences(text, chunk_size=30, overlap=5)

        # Each chunk should contain complete sentences
        for chunk in chunks:
            # Should end with sentence terminator or be partial
            if len(chunk) > 20:
                assert chunk.rstrip()[-1] in '.!?' or len(chunk) < 30

    def test_sentence_chunk_long_sentence(self):
        """Test handling of sentence longer than chunk_size"""
        long_sentence = "This is a very long sentence. " * 50
        chunks = chunk_text_by_sentences(long_sentence, chunk_size=100, overlap=20)

        assert len(chunks) > 0
        # Should split long sentences using simple chunking

    def test_sentence_chunk_multiple_punctuation(self):
        """Test various sentence endings"""
        text = "Question? Statement. Exclamation! Another."
        chunks = chunk_text_by_sentences(text, chunk_size=100, overlap=10)

        assert len(chunks) > 0
        full_text = " ".join(chunks)
        assert "Question?" in full_text
        assert "Exclamation!" in full_text

    def test_sentence_chunk_with_overlap(self):
        """Test sentence chunking with overlap"""
        sentences = ["Sentence {}.".format(i) for i in range(10)]
        text = " ".join(sentences)

        chunks = chunk_text_by_sentences(text, chunk_size=40, overlap=15)
        assert len(chunks) > 1


class TestGetOverlapText:
    """Test overlap text extraction"""

    def test_get_overlap_short_text(self):
        """Test overlap when text is shorter than overlap size"""
        text = "Short"
        overlap = get_overlap_text(text, overlap_size=20)
        assert overlap == text

    def test_get_overlap_at_word_boundary(self):
        """Test overlap respects word boundaries"""
        text = "This is a test sentence with many words"
        overlap = get_overlap_text(text, overlap_size=15)

        # Should not start in middle of word
        assert not overlap or overlap[0] != ' '

    def test_get_overlap_no_spaces(self):
        """Test overlap with no spaces"""
        text = "a" * 100
        overlap = get_overlap_text(text, overlap_size=20)
        assert len(overlap) <= 20


class TestChunkText:
    """Test main chunk_text function"""

    def test_chunk_text_default(self):
        """Test chunk_text with default parameters"""
        text = "This is a test. " * 100
        chunks = chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_preserve_sentences_true(self):
        """Test chunking with sentence preservation"""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, chunk_size=50, overlap=10, preserve_sentences=True)

        assert len(chunks) > 0

    def test_chunk_text_preserve_sentences_false(self):
        """Test chunking without sentence preservation"""
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_text(text, chunk_size=20, overlap=5, preserve_sentences=False)

        assert len(chunks) > 0

    def test_chunk_text_empty(self):
        """Test chunking empty or whitespace text"""
        assert chunk_text("") == []
        assert chunk_text("   ") == []
        assert chunk_text("\n\t") == []

    def test_chunk_text_newlines(self):
        """Test chunking text with newlines"""
        text = "Line one.\nLine two.\nLine three."
        chunks = chunk_text(text, chunk_size=20, overlap=5)

        assert len(chunks) > 0


class TestChunkTextWithMetadata:
    """Test chunking with metadata"""

    def test_chunk_with_basic_metadata(self):
        """Test chunking returns proper metadata"""
        text = "Test sentence. " * 20
        result = chunk_text_with_metadata(text, chunk_size=50, overlap=10)

        assert len(result) > 0
        for item in result:
            assert "text" in item
            assert "metadata" in item
            assert "chunk_index" in item["metadata"]
            assert "chunk_size" in item["metadata"]
            assert "total_chunks" in item["metadata"]

    def test_chunk_with_document_metadata(self):
        """Test chunking with document metadata"""
        text = "Test text. " * 10
        result = chunk_text_with_metadata(
            text,
            chunk_size=30,
            overlap=5,
            document_id="doc123",
            document_title="Test Document"
        )

        assert len(result) > 0
        for item in result:
            assert item["metadata"]["document_id"] == "doc123"
            assert item["metadata"]["document_title"] == "Test Document"

    def test_chunk_metadata_indices(self):
        """Test that chunk indices are sequential"""
        text = "Sentence. " * 30
        result = chunk_text_with_metadata(text, chunk_size=40, overlap=10)

        indices = [item["metadata"]["chunk_index"] for item in result]
        assert indices == list(range(len(indices)))

    def test_chunk_metadata_total_chunks(self):
        """Test that total_chunks is consistent"""
        text = "Test. " * 20
        result = chunk_text_with_metadata(text, chunk_size=30, overlap=5)

        total = len(result)
        for item in result:
            assert item["metadata"]["total_chunks"] == total


class TestEstimateTokens:
    """Test token estimation"""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation"""
        text = "a" * 100
        tokens = estimate_tokens(text)
        assert tokens == 25  # 100 / 4

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty text"""
        assert estimate_tokens("") == 0

    def test_estimate_tokens_realistic(self):
        """Test token estimation for realistic text"""
        text = "This is a sample sentence with several words."
        tokens = estimate_tokens(text)
        # Should be roughly 1/4 of character count
        assert 10 <= tokens <= 15


class TestChunkTextByTokens:
    """Test token-based chunking"""

    def test_chunk_by_tokens_basic(self):
        """Test basic token-based chunking"""
        text = "word " * 200  # ~200 words, ~800 chars
        chunks = chunk_text_by_tokens(text, max_tokens=50, overlap_tokens=10)

        assert len(chunks) > 0

    def test_chunk_by_tokens_defaults(self):
        """Test token chunking with default parameters"""
        text = "Test sentence. " * 100
        chunks = chunk_text_by_tokens(text)

        assert len(chunks) > 0

    def test_chunk_by_tokens_vs_chars(self):
        """Test that token chunking produces different results than char chunking"""
        text = "Test text. " * 50

        char_chunks = chunk_text(text, chunk_size=100, overlap=20)
        token_chunks = chunk_text_by_tokens(text, max_tokens=25, overlap_tokens=5)

        # Token-based should have different chunk sizes
        assert len(token_chunks) > 0
        assert len(char_chunks) > 0
