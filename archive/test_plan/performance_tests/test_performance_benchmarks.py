"""
Performance and Load Tests for Orchestrator 2.0

Tests performance benchmarks, parallel execution efficiency, memory usage,
and scalability under various load conditions.
"""

import pytest
import asyncio
import time
import psutil
import os
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, AsyncMock, Mock
from typing import List, Dict, Any
import statistics

from orchestrator_v2 import OrchestratorV2, OrchestratorConfig, PlanningStrategy
from orchestrator_integration import OrchestratorIntegration


class TestPerformanceBenchmarks:
    """Performance benchmark tests for Orchestrator 2.0"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Performance-optimized configuration
        self.config = OrchestratorConfig(
            max_parallel_steps=3,
            enable_streaming=True,
            enable_persistence=False,  # Disable for pure performance testing
            planning_strategy=PlanningStrategy.PARALLEL
        )
        
        # Mock LLM for consistent testing
        self.mock_llm = AsyncMock()
        self.mock_llm.ainvoke = AsyncMock(return_value=Mock(content=self._get_mock_plan()))
        
        # Setup mock document data
        self._setup_performance_mocks()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _get_mock_plan(self) -> str:
        """Get mock execution plan for testing"""
        return json.dumps({
            "plan": [
                {
                    "step_id": "step1",
                    "tool": "search_uploaded_docs",
                    "params": {"doc_name": "test_doc.pdf", "retrieve_full_doc": True},
                    "description": "Search document content"
                },
                {
                    "step_id": "step2", 
                    "tool": "extract_key_phrases",
                    "params": {"text": "$step1.output[0].page_content", "top_n": 10},
                    "dependencies": ["step1"],
                    "description": "Extract key phrases"
                },
                {
                    "step_id": "step3",
                    "tool": "synthesize_content", 
                    "params": {"chunks": "$step1", "method": "simple_llm_call", "length": "summary"},
                    "dependencies": ["step1"],
                    "description": "Create summary"
                }
            ]
        })
    
    def _setup_performance_mocks(self):
        """Setup performance-optimized mocks"""
        # Large document simulation
        self.large_document_chunks = []
        for i in range(100):  # 100 chunks
            self.large_document_chunks.append({
                "page_content": f"This is chunk {i} with substantial content to simulate real document processing. " * 10,
                "metadata": {"page": i+1, "chunk_id": i}
            })
        
        # Fast mock tools
        async def fast_search_docs(*args, **kwargs):
            await asyncio.sleep(0.01)  # Minimal delay
            return self.large_document_chunks[:10]  # Return subset for performance
        
        async def fast_extract_phrases(text: str, top_n: int = 10, **kwargs):
            await asyncio.sleep(0.02)  # Minimal processing time
            words = text.split()[:100]  # Limit processing
            return {
                "top_words": {f"word_{i}": i for i in range(min(top_n, len(words)))},
                "total_words": len(words)
            }
        
        async def fast_synthesize(chunks: List, **kwargs):
            await asyncio.sleep(0.05)  # Synthesis time
            return f"Summary of {len(chunks)} chunks with key findings."
        
        # Apply mocks
        self.search_mock = patch('tools.document_tools.search_uploaded_docs', side_effect=fast_search_docs)
        self.phrases_mock = patch('tools.text_analytics_tools.extract_key_phrases', side_effect=fast_extract_phrases)
        self.synthesis_mock = patch('tools.synthesis_tools.synthesize_content', side_effect=fast_synthesize)
    
    @pytest.mark.asyncio
    async def test_response_time_benchmark(self):
        """Test response time performance benchmarks"""
        with self.search_mock, self.phrases_mock, self.synthesis_mock:
            with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic', return_value=self.mock_llm):
                orchestrator = OrchestratorV2(self.config)
                
                # Single query benchmark
                start_time = time.time()
                
                result = await orchestrator.execute_query(
                    user_query="Analyze this document and extract key insights",
                    session_id="performance_test",
                    active_documents=["test_doc.pdf"]
                )
                
                execution_time = time.time() - start_time
                
                # Performance assertions
                assert result["status"] == "success"
                assert execution_time < 3.0, f"Response time {execution_time:.2f}s exceeds 3s target"
                
                # Verify execution efficiency
                summary = result.get("execution_summary", {})
                assert summary.get("success_rate", 0) >= 0.8, "Success rate below 80%"
    
    @pytest.mark.asyncio
    async def test_parallel_execution_efficiency(self):
        """Test parallel execution performance vs sequential"""
        with self.search_mock, self.phrases_mock, self.synthesis_mock:
            with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic', return_value=self.mock_llm):
                # Test parallel strategy
                parallel_config = OrchestratorConfig(
                    max_parallel_steps=3,
                    planning_strategy=PlanningStrategy.PARALLEL
                )
                parallel_orchestrator = OrchestratorV2(parallel_config)
                
                # Test sequential strategy
                sequential_config = OrchestratorConfig(
                    max_parallel_steps=1,
                    planning_strategy=PlanningStrategy.SIMPLE
                )
                sequential_orchestrator = OrchestratorV2(sequential_config)
                
                query = "Comprehensive analysis with multiple processing steps"
                session_base = "efficiency_test"
                docs = ["test_doc.pdf"]
                
                # Measure parallel execution
                start_time = time.time()
                parallel_result = await parallel_orchestrator.execute_query(
                    user_query=query,
                    session_id=f"{session_base}_parallel",
                    active_documents=docs
                )
                parallel_time = time.time() - start_time
                
                # Measure sequential execution
                start_time = time.time()
                sequential_result = await sequential_orchestrator.execute_query(
                    user_query=query,
                    session_id=f"{session_base}_sequential", 
                    active_documents=docs
                )
                sequential_time = time.time() - start_time
                
                # Performance comparison
                assert parallel_result["status"] == "success"
                assert sequential_result["status"] == "success"
                
                # Parallel should be faster (allow some variance)
                speedup = sequential_time / parallel_time if parallel_time > 0 else 1
                assert speedup >= 1.2, f"Parallel speedup {speedup:.2f}x is less than 1.2x"
                
                print(f"Parallel: {parallel_time:.2f}s, Sequential: {sequential_time:.2f}s, Speedup: {speedup:.2f}x")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_load(self):
        """Test system performance under concurrent user load"""
        with self.search_mock, self.phrases_mock, self.synthesis_mock:
            with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic', return_value=self.mock_llm):
                orchestrator = OrchestratorV2(self.config)
                
                concurrent_users = 10
                queries_per_user = 3
                
                async def user_simulation(user_id: int) -> List[Dict]:
                    """Simulate individual user with multiple queries"""
                    user_results = []
                    session_id = f"load_test_user_{user_id}"
                    
                    for query_num in range(queries_per_user):
                        start_time = time.time()
                        
                        try:
                            result = await orchestrator.execute_query(
                                user_query=f"User {user_id} query {query_num}: Analyze document",
                                session_id=session_id,
                                active_documents=["test_doc.pdf"]
                            )
                            
                            execution_time = time.time() - start_time
                            
                            user_results.append({
                                "user_id": user_id,
                                "query_num": query_num,
                                "success": result["status"] == "success",
                                "execution_time": execution_time,
                                "confidence": result.get("confidence_score", 0)
                            })
                            
                        except Exception as e:
                            user_results.append({
                                "user_id": user_id,
                                "query_num": query_num,
                                "success": False,
                                "execution_time": time.time() - start_time,
                                "error": str(e)
                            })
                    
                    return user_results
                
                # Run concurrent user simulations
                start_time = time.time()
                
                tasks = [user_simulation(i) for i in range(concurrent_users)]
                all_results = await asyncio.gather(*tasks)
                
                total_time = time.time() - start_time
                
                # Analyze results
                flat_results = [result for user_results in all_results for result in user_results]
                successful_queries = [r for r in flat_results if r["success"]]
                
                # Performance metrics
                success_rate = len(successful_queries) / len(flat_results) * 100
                avg_response_time = statistics.mean([r["execution_time"] for r in successful_queries])
                max_response_time = max([r["execution_time"] for r in successful_queries])
                throughput = len(flat_results) / total_time  # queries per second
                
                # Performance assertions
                assert success_rate >= 90.0, f"Success rate {success_rate:.1f}% below 90%"
                assert avg_response_time <= 5.0, f"Average response time {avg_response_time:.2f}s above 5s"
                assert max_response_time <= 15.0, f"Max response time {max_response_time:.2f}s above 15s"
                assert throughput >= 2.0, f"Throughput {throughput:.2f} queries/s below 2.0"
                
                print(f"Load Test Results:")
                print(f"  Users: {concurrent_users}, Queries: {len(flat_results)}")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Avg Response Time: {avg_response_time:.2f}s")
                print(f"  Max Response Time: {max_response_time:.2f}s")
                print(f"  Throughput: {throughput:.2f} queries/s")
    
    def test_memory_usage_performance(self):
        """Test memory usage under various loads"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with self.search_mock, self.phrases_mock, self.synthesis_mock:
            with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic', return_value=self.mock_llm):
                orchestrators = []
                
                # Create multiple orchestrator instances
                for i in range(5):
                    config = OrchestratorConfig(
                        enable_persistence=False,  # Minimize memory overhead
                        max_parallel_steps=2
                    )
                    orchestrator = OrchestratorV2(config)
                    orchestrators.append(orchestrator)
                
                # Run queries on each instance
                async def run_memory_test():
                    tasks = []
                    for i, orch in enumerate(orchestrators):
                        task = orch.execute_query(
                            user_query=f"Memory test query {i}",
                            session_id=f"memory_test_{i}",
                            active_documents=["test_doc.pdf"]
                        )
                        tasks.append(task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    return results
                
                # Execute memory test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    results = loop.run_until_complete(run_memory_test())
                finally:
                    loop.close()
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                # Memory usage assertions
                assert memory_increase <= 200, f"Memory increase {memory_increase:.1f}MB exceeds 200MB limit"
                
                # Verify results
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) >= 4, "Less than 4 successful executions"
                
                print(f"Memory Usage:")
                print(f"  Initial: {initial_memory:.1f}MB")
                print(f"  Final: {final_memory:.1f}MB") 
                print(f"  Increase: {memory_increase:.1f}MB")
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self):
        """Test streaming performance and responsiveness"""
        with self.search_mock, self.phrases_mock, self.synthesis_mock:
            with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic', return_value=self.mock_llm):
                orchestrator = OrchestratorV2(self.config)
                
                updates = []
                timestamps = []
                start_time = time.time()
                
                async for update in orchestrator.execute_query_streaming(
                    user_query="Stream performance test query",
                    session_id="streaming_perf_test",
                    active_documents=["test_doc.pdf"]
                ):
                    current_time = time.time() - start_time
                    updates.append(update)
                    timestamps.append(current_time)
                
                total_time = timestamps[-1] if timestamps else 0
                
                # Performance assertions
                assert len(updates) >= 3, "Insufficient streaming updates"
                assert total_time <= 5.0, f"Total streaming time {total_time:.2f}s exceeds 5s"
                
                # First update should arrive quickly
                if timestamps:
                    first_update_time = timestamps[0]
                    assert first_update_time <= 1.0, f"First update took {first_update_time:.2f}s"
                
                # Updates should be reasonably spaced
                if len(timestamps) > 1:
                    update_intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                    max_interval = max(update_intervals)
                    assert max_interval <= 3.0, f"Max update interval {max_interval:.2f}s too long"
                
                print(f"Streaming Performance:")
                print(f"  Total Updates: {len(updates)}")
                print(f"  Total Time: {total_time:.2f}s")
                print(f"  First Update: {timestamps[0]:.2f}s" if timestamps else "  No updates")


class TestScalabilityTests:
    """Scalability tests for production deployment"""
    
    def setup_method(self):
        """Setup scalability test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup mocks for consistent testing
        self._setup_scalability_mocks()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_scalability_mocks(self):
        """Setup mocks for scalability testing"""
        async def mock_tool(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate realistic processing time
            return {"result": "mock_output"}
        
        self.tool_mocks = [
            patch('tools.document_tools.search_uploaded_docs', side_effect=mock_tool),
            patch('tools.synthesis_tools.synthesize_content', side_effect=mock_tool),
            patch('tools.text_analytics_tools.extract_key_phrases', side_effect=mock_tool)
        ]
    
    @pytest.mark.asyncio
    async def test_high_concurrency_scalability(self):
        """Test system scalability with high concurrency"""
        concurrent_sessions = 20
        queries_per_session = 5
        
        with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=Mock(content='{"plan": [{"step_id": "step1", "tool": "search_uploaded_docs", "params": {"doc_name": "test.pdf"}}]}'))
            mock_llm_class.return_value = mock_llm
            
            with self.tool_mocks[0], self.tool_mocks[1], self.tool_mocks[2]:
                # Use integration layer for realistic testing
                integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=False)
                
                async def session_simulation(session_id: int):
                    """Simulate a complete user session"""
                    session_results = []
                    
                    for query_num in range(queries_per_session):
                        start_time = time.time()
                        
                        try:
                            result = await integration.run(
                                user_query=f"Session {session_id} query {query_num}",
                                session_id=f"scalability_session_{session_id}",
                                active_documents=["test.pdf"]
                            )
                            
                            execution_time = time.time() - start_time
                            
                            session_results.append({
                                "session_id": session_id,
                                "query_num": query_num,
                                "success": result.get("status") == "success",
                                "execution_time": execution_time
                            })
                            
                        except Exception as e:
                            session_results.append({
                                "session_id": session_id,
                                "query_num": query_num,
                                "success": False,
                                "execution_time": time.time() - start_time,
                                "error": str(e)
                            })
                    
                    return session_results
                
                # Execute high concurrency test
                start_time = time.time()
                
                tasks = [session_simulation(i) for i in range(concurrent_sessions)]
                all_session_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                total_execution_time = time.time() - start_time
                
                # Process results
                successful_sessions = [r for r in all_session_results if not isinstance(r, Exception)]
                all_queries = []
                for session_result in successful_sessions:
                    all_queries.extend(session_result)
                
                successful_queries = [q for q in all_queries if q["success"]]
                
                # Scalability metrics
                total_queries = len(all_queries)
                success_rate = len(successful_queries) / total_queries * 100 if total_queries > 0 else 0
                throughput = total_queries / total_execution_time
                avg_response_time = statistics.mean([q["execution_time"] for q in successful_queries]) if successful_queries else 0
                
                # Scalability assertions
                assert success_rate >= 85.0, f"High concurrency success rate {success_rate:.1f}% below 85%"
                assert throughput >= 5.0, f"Throughput {throughput:.2f} queries/s below 5.0"
                assert avg_response_time <= 10.0, f"Avg response time {avg_response_time:.2f}s above 10s"
                
                print(f"High Concurrency Scalability Results:")
                print(f"  Sessions: {concurrent_sessions}, Total Queries: {total_queries}")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Throughput: {throughput:.2f} queries/s")
                print(f"  Avg Response Time: {avg_response_time:.2f}s")
    
    @pytest.mark.asyncio
    async def test_resource_efficiency_scaling(self):
        """Test resource efficiency as load scales"""
        load_levels = [1, 5, 10, 15]  # Number of concurrent users
        efficiency_metrics = []
        
        with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=Mock(content='{"plan": [{"step_id": "step1", "tool": "search_uploaded_docs", "params": {"doc_name": "test.pdf"}}]}'))
            mock_llm_class.return_value = mock_llm
            
            with self.tool_mocks[0], self.tool_mocks[1], self.tool_mocks[2]:
                for load_level in load_levels:
                    # Measure resource usage at each load level
                    process = psutil.Process(os.getpid())
                    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                    
                    integration = OrchestratorIntegration(enable_v2=True, fallback_to_v1=False)
                    
                    async def load_simulation(user_id: int):
                        return await integration.run(
                            user_query=f"Load test query from user {user_id}",
                            session_id=f"load_user_{user_id}",
                            active_documents=["test.pdf"]
                        )
                    
                    # Execute load
                    start_time = time.time()
                    
                    tasks = [load_simulation(i) for i in range(load_level)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    execution_time = time.time() - start_time
                    final_memory = process.memory_info().rss / 1024 / 1024  # MB
                    
                    # Calculate metrics
                    successful_results = [r for r in results if not isinstance(r, Exception)]
                    success_rate = len(successful_results) / len(results) * 100
                    memory_per_user = (final_memory - initial_memory) / load_level if load_level > 0 else 0
                    throughput = load_level / execution_time
                    
                    efficiency_metrics.append({
                        "load_level": load_level,
                        "success_rate": success_rate,
                        "memory_per_user": memory_per_user,
                        "throughput": throughput,
                        "execution_time": execution_time
                    })
                
                # Analyze scaling efficiency
                for i, metrics in enumerate(efficiency_metrics):
                    load = metrics["load_level"]
                    success_rate = metrics["success_rate"]
                    memory_per_user = metrics["memory_per_user"]
                    throughput = metrics["throughput"]
                    
                    # Efficiency assertions
                    assert success_rate >= 80.0, f"Load {load}: Success rate {success_rate:.1f}% below 80%"
                    assert memory_per_user <= 50.0, f"Load {load}: Memory per user {memory_per_user:.1f}MB above 50MB"
                    assert throughput >= 1.0, f"Load {load}: Throughput {throughput:.2f} below 1.0"
                    
                    print(f"Load Level {load}: Success {success_rate:.1f}%, Memory/User {memory_per_user:.1f}MB, Throughput {throughput:.2f}")


class TestResourceUtilization:
    """Tests for resource utilization optimization"""
    
    @pytest.mark.asyncio
    async def test_cpu_utilization_efficiency(self):
        """Test CPU utilization efficiency"""
        with patch('orchestrator_v2.orchestrator_v2.ChatAnthropic') as mock_llm_class:
            mock_llm = AsyncMock()
            mock_llm.ainvoke = AsyncMock(return_value=Mock(content='{"plan": [{"step_id": "step1", "tool": "search_uploaded_docs", "params": {"doc_name": "test.pdf"}}]}'))
            mock_llm_class.return_value = mock_llm
            
            config = OrchestratorConfig(max_parallel_steps=4)  # Use multiple cores
            orchestrator = OrchestratorV2(config)
            
            # Mock CPU-intensive tools
            async def cpu_intensive_tool(*args, **kwargs):
                # Simulate CPU work
                await asyncio.sleep(0.1)
                return {"result": "processed"}
            
            with patch('tools.document_tools.search_uploaded_docs', side_effect=cpu_intensive_tool):
                with patch('tools.synthesis_tools.synthesize_content', side_effect=cpu_intensive_tool):
                    
                    # Monitor CPU usage
                    initial_cpu = psutil.cpu_percent(interval=1)
                    
                    # Execute parallel workload
                    tasks = []
                    for i in range(8):  # More tasks than parallel slots
                        task = orchestrator.execute_query(
                            user_query=f"CPU test query {i}",
                            session_id=f"cpu_test_{i}",
                            active_documents=["test.pdf"]
                        )
                        tasks.append(task)
                    
                    start_time = time.time()
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    execution_time = time.time() - start_time
                    
                    final_cpu = psutil.cpu_percent(interval=1)
                    
                    # Analyze results
                    successful_results = [r for r in results if not isinstance(r, Exception)]
                    
                    # CPU efficiency assertions
                    assert len(successful_results) >= 6, "Less than 75% success rate"
                    assert execution_time <= 8.0, f"Execution time {execution_time:.2f}s too high"
                    
                    # Should utilize available CPU cores efficiently
                    cpu_cores = psutil.cpu_count()
                    expected_parallel_time = 2.0  # Assuming 4 batches of 2 tasks each at 0.5s per batch
                    efficiency = expected_parallel_time / execution_time if execution_time > 0 else 0
                    
                    assert efficiency >= 0.6, f"CPU efficiency {efficiency:.2f} below 60%"
                    
                    print(f"CPU Utilization Test:")
                    print(f"  Tasks: {len(tasks)}, Successful: {len(successful_results)}")
                    print(f"  Execution Time: {execution_time:.2f}s")
                    print(f"  CPU Efficiency: {efficiency:.2f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])