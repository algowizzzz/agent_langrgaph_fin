#!/usr/bin/env python3
"""
Test Runner for Orchestrator 2.0 Test Suite

Comprehensive test execution with reporting and validation.
Supports different test phases and generates detailed reports.
"""

import pytest
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse


class TestRunner:
    """Main test runner for Orchestrator 2.0 test suite"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.results_dir = self.base_dir / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test phases configuration
        self.test_phases = {
            "unit": {
                "name": "Unit Tests",
                "description": "Core component validation",
                "path": "unit_tests/",
                "critical": True,
                "min_coverage": 95
            },
            "integration": {
                "name": "Integration Tests", 
                "description": "Component interaction validation",
                "path": "integration_tests/",
                "critical": True,
                "min_success_rate": 98
            },
            "performance": {
                "name": "Performance Tests",
                "description": "Performance benchmarks and scalability",
                "path": "performance_tests/",
                "critical": False,
                "min_success_rate": 90
            },
            "business": {
                "name": "Business Validation Tests",
                "description": "Business scenarios and acceptance criteria",
                "path": "business_tests/",
                "critical": True,
                "min_success_rate": 95
            }
        }
    
    def run_phase(self, phase: str, verbose: bool = False) -> Dict[str, Any]:
        """Run a specific test phase"""
        if phase not in self.test_phases:
            raise ValueError(f"Unknown test phase: {phase}")
        
        phase_config = self.test_phases[phase]
        test_path = self.base_dir / phase_config["path"]
        
        print(f"\n{'='*60}")
        print(f"🧪 Running {phase_config['name']}")
        print(f"📋 {phase_config['description']}")
        print(f"📁 Path: {test_path}")
        print(f"{'='*60}")
        
        if not test_path.exists():
            print(f"⚠️  Test path does not exist: {test_path}")
            return {
                "phase": phase,
                "status": "skipped",
                "reason": "path_not_found",
                "start_time": time.time(),
                "end_time": time.time(),
                "duration": 0,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        
        # Prepare pytest arguments
        pytest_args = [
            str(test_path),
            "--tb=short",
            "--no-header",
            f"--junit-xml={self.results_dir}/{phase}_results.xml"
        ]
        
        if verbose:
            pytest_args.extend(["-v", "-s"])
        
        # Add coverage for unit tests
        if phase == "unit":
            pytest_args.extend([
                "--cov=orchestrator_v2",
                "--cov-report=html",
                f"--cov-report=xml:{self.results_dir}/coverage.xml",
                "--cov-fail-under=90"
            ])
        
        # Run tests
        start_time = time.time()
        
        try:
            exit_code = pytest.main(pytest_args)
            end_time = time.time()
            
            # Parse results
            result = self._parse_test_results(phase, exit_code, start_time, end_time)
            
            # Generate phase report
            self._generate_phase_report(phase, result)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            return {
                "phase": phase,
                "status": "error",
                "error": str(e),
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
    
    def run_all_phases(self, skip_non_critical: bool = False, verbose: bool = False) -> Dict[str, Any]:
        """Run all test phases"""
        print(f"\n🚀 Starting Orchestrator 2.0 Test Suite")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        overall_start = time.time()
        phase_results = {}
        
        for phase_name, phase_config in self.test_phases.items():
            if skip_non_critical and not phase_config.get("critical", True):
                print(f"\n⏭️  Skipping non-critical phase: {phase_config['name']}")
                continue
            
            try:
                result = self.run_phase(phase_name, verbose)
                phase_results[phase_name] = result
                
                # Check if critical phase failed
                if phase_config.get("critical") and result["status"] == "failed":
                    print(f"\n❌ Critical phase '{phase_name}' failed!")
                    
                    if not self._should_continue_after_failure():
                        print("🛑 Stopping test execution due to critical failure")
                        break
                
            except KeyboardInterrupt:
                print(f"\n⚠️  Test execution interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error running phase '{phase_name}': {e}")
                phase_results[phase_name] = {
                    "phase": phase_name,
                    "status": "error",
                    "error": str(e)
                }
        
        overall_end = time.time()
        
        # Generate comprehensive report
        summary = self._generate_summary_report(phase_results, overall_start, overall_end)
        
        return summary
    
    def _parse_test_results(self, phase: str, exit_code: int, start_time: float, end_time: float) -> Dict[str, Any]:
        """Parse test results from pytest execution"""
        duration = end_time - start_time
        
        # Basic result based on exit code
        status = "passed" if exit_code == 0 else "failed"
        
        # Try to parse JUnit XML for detailed results
        junit_file = self.results_dir / f"{phase}_results.xml"
        tests_run = 0
        tests_passed = 0 
        tests_failed = 0
        
        if junit_file.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(junit_file)
                root = tree.getroot()
                
                # Parse JUnit XML
                for testsuite in root.findall('.//testsuite'):
                    tests_run += int(testsuite.get('tests', 0))
                    tests_passed += int(testsuite.get('tests', 0)) - int(testsuite.get('failures', 0)) - int(testsuite.get('errors', 0))
                    tests_failed += int(testsuite.get('failures', 0)) + int(testsuite.get('errors', 0))
                    
            except Exception as e:
                print(f"⚠️  Could not parse JUnit results: {e}")
        
        return {
            "phase": phase,
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "success_rate": (tests_passed / tests_run * 100) if tests_run > 0 else 0,
            "exit_code": exit_code
        }
    
    def _generate_phase_report(self, phase: str, result: Dict[str, Any]) -> None:
        """Generate individual phase report"""
        phase_config = self.test_phases[phase]
        
        print(f"\n📊 {phase_config['name']} Results:")
        print(f"   Status: {'✅' if result['status'] == 'passed' else '❌'} {result['status'].upper()}")
        print(f"   Duration: {result['duration']:.2f}s")
        print(f"   Tests Run: {result['tests_run']}")
        print(f"   Passed: {result['tests_passed']}")
        print(f"   Failed: {result['tests_failed']}")
        
        if result['tests_run'] > 0:
            print(f"   Success Rate: {result['success_rate']:.1f}%")
            
            # Check against minimum requirements
            min_success_rate = phase_config.get("min_success_rate", 95)
            if result['success_rate'] < min_success_rate:
                print(f"   ⚠️  Below minimum success rate of {min_success_rate}%")
        
        # Save detailed results
        result_file = self.results_dir / f"{phase}_detailed_results.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def _generate_summary_report(self, phase_results: Dict[str, Any], start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        total_duration = end_time - start_time
        
        # Calculate overall metrics
        total_tests = sum(r.get("tests_run", 0) for r in phase_results.values())
        total_passed = sum(r.get("tests_passed", 0) for r in phase_results.values())
        total_failed = sum(r.get("tests_failed", 0) for r in phase_results.values())
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Check critical phase status
        critical_phases_passed = True
        for phase_name, result in phase_results.items():
            phase_config = self.test_phases[phase_name]
            if phase_config.get("critical") and result.get("status") != "passed":
                critical_phases_passed = False
                break
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": overall_success_rate,
            "critical_phases_passed": critical_phases_passed,
            "phase_results": phase_results,
            "production_ready": self._assess_production_readiness(phase_results)
        }
        
        # Print summary
        self._print_summary(summary)
        
        # Save summary report
        summary_file = self.results_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    def _assess_production_readiness(self, phase_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess production readiness based on test results"""
        readiness = {
            "ready": True,
            "score": 100,
            "issues": [],
            "recommendations": []
        }
        
        for phase_name, result in phase_results.items():
            phase_config = self.test_phases[phase_name]
            
            # Check critical phases
            if phase_config.get("critical") and result.get("status") != "passed":
                readiness["ready"] = False
                readiness["score"] -= 30
                readiness["issues"].append(f"Critical phase '{phase_name}' failed")
            
            # Check success rates
            min_success_rate = phase_config.get("min_success_rate", 95)
            actual_rate = result.get("success_rate", 0)
            
            if actual_rate < min_success_rate:
                severity = "HIGH" if phase_config.get("critical") else "MEDIUM"
                readiness["issues"].append(f"{severity}: {phase_name} success rate {actual_rate:.1f}% below {min_success_rate}%")
                
                if phase_config.get("critical"):
                    readiness["ready"] = False
                    readiness["score"] -= 20
                else:
                    readiness["score"] -= 10
        
        # Recommendations
        if not readiness["ready"]:
            readiness["recommendations"].append("Address critical test failures before production deployment")
        
        if readiness["score"] < 90:
            readiness["recommendations"].append("Improve test success rates and address failing scenarios")
        
        if readiness["score"] >= 95:
            readiness["recommendations"].append("System is ready for production deployment")
        elif readiness["score"] >= 85:
            readiness["recommendations"].append("System ready for staging deployment with monitoring")
        
        return readiness
    
    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print test execution summary"""
        print(f"\n{'='*60}")
        print(f"📋 ORCHESTRATOR 2.0 TEST SUMMARY")
        print(f"{'='*60}")
        
        print(f"🕒 Total Duration: {summary['total_duration']:.2f}s")
        print(f"🧪 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['total_passed']}")
        print(f"❌ Failed: {summary['total_failed']}")
        print(f"📊 Success Rate: {summary['overall_success_rate']:.1f}%")
        
        # Phase breakdown
        print(f"\n📋 Phase Results:")
        for phase_name, result in summary['phase_results'].items():
            status_icon = "✅" if result.get("status") == "passed" else "❌"
            success_rate = result.get("success_rate", 0)
            print(f"   {status_icon} {self.test_phases[phase_name]['name']}: {success_rate:.1f}% ({result.get('tests_passed', 0)}/{result.get('tests_run', 0)})")
        
        # Production readiness assessment
        readiness = summary['production_ready']
        print(f"\n🚀 Production Readiness Assessment:")
        print(f"   Ready: {'✅ YES' if readiness['ready'] else '❌ NO'}")
        print(f"   Score: {readiness['score']}/100")
        
        if readiness['issues']:
            print(f"   Issues:")
            for issue in readiness['issues']:
                print(f"     • {issue}")
        
        if readiness['recommendations']:
            print(f"   Recommendations:")
            for rec in readiness['recommendations']:
                print(f"     • {rec}")
        
        print(f"\n📁 Detailed results saved to: {self.results_dir}")
        print(f"{'='*60}")
    
    def _should_continue_after_failure(self) -> bool:
        """Ask user whether to continue after critical failure"""
        try:
            response = input("\nContinue with remaining tests? (y/N): ")
            return response.lower().startswith('y')
        except (EOFError, KeyboardInterrupt):
            return False


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description="Orchestrator 2.0 Test Runner")
    parser.add_argument("--phase", choices=["unit", "integration", "performance", "business"], 
                       help="Run specific test phase")
    parser.add_argument("--skip-non-critical", action="store_true",
                       help="Skip non-critical test phases")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose test output")
    parser.add_argument("--results-dir", 
                       help="Directory for test results")
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(base_dir=args.results_dir)
    
    try:
        if args.phase:
            # Run specific phase
            result = runner.run_phase(args.phase, args.verbose)
            sys.exit(0 if result["status"] == "passed" else 1)
        else:
            # Run all phases
            summary = runner.run_all_phases(args.skip_non_critical, args.verbose)
            
            # Exit with appropriate code
            if summary["critical_phases_passed"] and summary["overall_success_rate"] >= 95:
                sys.exit(0)  # Success
            else:
                sys.exit(1)  # Failure
                
    except KeyboardInterrupt:
        print("\n🛑 Test execution interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()