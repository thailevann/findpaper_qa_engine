#!/usr/bin/env node

/**
 * Simple integration test for FindPaper QA Engine Frontend
 * Tests the API connection and basic functionality
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

async function testHealthCheck() {
  console.log('🔍 Testing health check...')
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    if (response.ok) {
      const data = await response.json()
      console.log('✅ Health check passed:', data)
      return true
    } else {
      console.log('❌ Health check failed:', response.status)
      return false
    }
  } catch (error) {
    console.log('❌ Health check error:', error.message)
    return false
  }
}

async function testQAEndpoint() {
  console.log('\n🔍 Testing QA endpoint...')
  try {
    const testQuery = {
      query: "What are the latest advances in machine learning?",
      limit: 10,
      max_themes: 3,
      model: "gpt-4o-mini"
    }

    const response = await fetch(`${API_BASE_URL}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testQuery)
    })

    if (response.ok) {
      const data = await response.json()
      console.log('✅ QA endpoint test passed')
      console.log(`📊 Found ${data.finding_info.total_passages_found} passages`)
      console.log(`📝 Selected ${data.qa_result.processing_info.selected_quotes} quotes`)
      console.log(`🎯 Generated ${data.qa_result.processing_info.themes_generated} themes`)
      console.log(`📄 Answer length: ${data.qa_result.final_report.length} characters`)
      return true
    } else {
      const errorText = await response.text()
      console.log('❌ QA endpoint test failed:', response.status, errorText)
      return false
    }
  } catch (error) {
    console.log('❌ QA endpoint error:', error.message)
    return false
  }
}

async function testSearchPassages() {
  console.log('\n🔍 Testing search passages endpoint...')
  try {
    const testQuery = {
      query: "machine learning",
      limit: 5
    }

    const response = await fetch(`${API_BASE_URL}/search_passsages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testQuery)
    })

    if (response.ok) {
      const data = await response.json()
      console.log('✅ Search passages test passed')
      console.log(`📊 Found ${data.matched_count} passages`)
      return true
    } else {
      const errorText = await response.text()
      console.log('❌ Search passages test failed:', response.status, errorText)
      return false
    }
  } catch (error) {
    console.log('❌ Search passages error:', error.message)
    return false
  }
}

async function runTests() {
  console.log('🚀 Starting FindPaper QA Engine Frontend Integration Tests')
  console.log('=' .repeat(60))
  console.log(`🌐 API Base URL: ${API_BASE_URL}`)
  console.log('=' .repeat(60))

  const results = {
    health: await testHealthCheck(),
    qa: await testQAEndpoint(),
    search: await testSearchPassages()
  }

  console.log('\n' + '=' .repeat(60))
  console.log('📊 Test Results Summary:')
  console.log('=' .repeat(60))
  console.log(`Health Check: ${results.health ? '✅ PASS' : '❌ FAIL'}`)
  console.log(`QA Endpoint: ${results.qa ? '✅ PASS' : '❌ FAIL'}`)
  console.log(`Search Passages: ${results.search ? '✅ PASS' : '❌ FAIL'}`)
  
  const allPassed = Object.values(results).every(result => result)
  console.log('\n' + '=' .repeat(60))
  console.log(`Overall Result: ${allPassed ? '🎉 ALL TESTS PASSED' : '⚠️  SOME TESTS FAILED'}`)
  console.log('=' .repeat(60))

  if (!allPassed) {
    console.log('\n💡 Troubleshooting Tips:')
    console.log('1. Make sure the backend is running: python app.py')
    console.log('2. Check if the API URL is correct:', API_BASE_URL)
    console.log('3. Verify environment variables are set correctly')
    console.log('4. Check backend logs for any errors')
  }

  process.exit(allPassed ? 0 : 1)
}

// Run tests if this script is executed directly
if (require.main === module) {
  runTests().catch(console.error)
}

module.exports = { testHealthCheck, testQAEndpoint, testSearchPassages }
