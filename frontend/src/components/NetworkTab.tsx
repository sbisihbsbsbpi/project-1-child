// @ts-nocheck
import React, { useState, useEffect } from "react";
import { config } from "../config";

interface NetworkTabProps {
  addNotification: (notification: any) => void;
}

interface InterceptedAPI {
  id: string;
  method: string;
  url: string;
  status: number;
  statusText: string;
  timestamp: number;
  request_headers: Record<string, string>;
  response_headers: Record<string, string>;
  request_body: string | null;
  response_body: string;
  response_json: any;
  captured_at: number;
  page_url?: string;
  captured_from?: string;
}

function NetworkTabComponent({ addNotification }: NetworkTabProps) {
  const [activeSection, setActiveSection] = useState<
    "extract" | "metadata" | "validate" | "compare"
  >("extract");

  // ✅ NEW: Intercepted APIs state
  const [interceptedApis, setInterceptedApis] = useState<InterceptedAPI[]>([]);
  const [selectedApiId, setSelectedApiId] = useState<string>("");
  const [loadingApis, setLoadingApis] = useState(false);
  const [showManualInput, setShowManualInput] = useState(false);

  // ✅ NEW: Filter state
  const [methodFilter, setMethodFilter] = useState<string>("ALL");
  const [urlFilter, setUrlFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // API Extraction state
  const [extractUrl, setExtractUrl] = useState("");
  const [apiPattern, setApiPattern] = useState("");
  const [extracting, setExtracting] = useState(false);

  // Metadata Generation state
  const [apiResponse, setApiResponse] = useState("");
  const [generatedMetadata, setGeneratedMetadata] = useState<any>(null);
  const [metadataPrefix, setMetadataPrefix] = useState("data");
  const [generating, setGenerating] = useState(false);

  // Field Extraction state
  const [responseData, setResponseData] = useState("");
  const [fieldMappings, setFieldMappings] = useState("");
  const [extractedFields, setExtractedFields] = useState<any>(null);
  const [extractingFields, setExtractingFields] = useState(false);

  // Validation state
  const [validationResponse, setValidationResponse] = useState("");
  const [validationMetadata, setValidationMetadata] = useState("");
  const [validationResult, setValidationResult] = useState<any>(null);
  const [validating, setValidating] = useState(false);

  // Environment Comparison state
  const [devExtraction, setDevExtraction] = useState("");
  const [stagingExtraction, setStagingExtraction] = useState("");
  const [prodExtraction, setProdExtraction] = useState("");
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [comparing, setComparing] = useState(false);

  // ✅ NEW: Load intercepted APIs on mount
  useEffect(() => {
    loadInterceptedApis();
  }, []);

  // ✅ NEW: Load intercepted APIs from backend
  const loadInterceptedApis = async () => {
    try {
      setLoadingApis(true);
      const response = await fetch(
        `${config.apiBaseUrl}/api/network/intercepted-apis`
      );
      const result = await response.json();

      if (result.success) {
        setInterceptedApis(result.apis || []);
      }
    } catch (error: any) {
      console.error("Failed to load intercepted APIs:", error);
    } finally {
      setLoadingApis(false);
    }
  };

  // ✅ NEW: Clear all intercepted APIs
  const handleClearApis = async () => {
    try {
      const response = await fetch(
        `${config.apiBaseUrl}/api/network/intercepted-apis`,
        {
          method: "DELETE",
        }
      );
      const result = await response.json();

      if (result.success) {
        setInterceptedApis([]);
        setSelectedApiId("");
        setApiResponse("");
        addNotification({
          type: "success",
          title: "✅ APIs Cleared",
          message: result.message,
          duration: 3000,
        });
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Clear Failed",
        message: error.message,
        duration: 5000,
      });
    }
  };

  // ✅ NEW: Delete individual API
  const handleDeleteApi = async (apiId: string) => {
    try {
      const response = await fetch(
        `${config.apiBaseUrl}/api/network/intercepted-apis/${apiId}`,
        {
          method: "DELETE",
        }
      );
      const result = await response.json();

      if (result.success) {
        // Remove from local state
        setInterceptedApis((prev) => prev.filter((api) => api.id !== apiId));

        // Clear selection if deleted API was selected
        if (selectedApiId === apiId) {
          setSelectedApiId("");
          setApiResponse("");
        }

        addNotification({
          type: "success",
          title: "✅ API Deleted",
          message: "API removed successfully",
          duration: 2000,
        });
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Delete Failed",
        message: error.message,
        duration: 5000,
      });
    }
  };

  // ✅ NEW: Filter intercepted APIs
  const filteredApis = interceptedApis.filter((api) => {
    // Filter by method
    if (methodFilter !== "ALL" && api.method !== methodFilter) {
      return false;
    }

    // Filter by URL pattern
    if (urlFilter && !api.url.toLowerCase().includes(urlFilter.toLowerCase())) {
      return false;
    }

    // Filter by status code
    if (statusFilter !== "ALL") {
      const status = api.status;
      if (statusFilter === "2xx" && (status < 200 || status >= 300))
        return false;
      if (statusFilter === "3xx" && (status < 300 || status >= 400))
        return false;
      if (statusFilter === "4xx" && (status < 400 || status >= 500))
        return false;
      if (statusFilter === "5xx" && (status < 500 || status >= 600))
        return false;
    }

    return true;
  });

  // ✅ Get unique methods from intercepted APIs
  const uniqueMethods = Array.from(
    new Set(interceptedApis.map((api) => api.method))
  ).sort();

  // ✅ NEW: Handle API selection from dropdown
  const handleApiSelection = (apiId: string) => {
    setSelectedApiId(apiId);
    const selectedApi = interceptedApis.find((api) => api.id === apiId);
    if (selectedApi && selectedApi.response_json) {
      setApiResponse(JSON.stringify(selectedApi.response_json, null, 2));
    }
  };

  // ✅ NEW: Add manual API
  const handleAddManualApi = async () => {
    try {
      const parsedResponse = JSON.parse(apiResponse);

      const response = await fetch(
        `${config.apiBaseUrl}/api/network/add-manual-api`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: "/api/manual",
            method: "GET",
            status: 200,
            response_json: parsedResponse,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        await loadInterceptedApis();
        addNotification({
          type: "success",
          title: "✅ API Added",
          message: "Manual API added successfully",
          duration: 3000,
        });
        setShowManualInput(false);
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Add Failed",
        message: error.message,
        duration: 5000,
      });
    }
  };

  // Generate Metadata from API Response
  const handleGenerateMetadata = async () => {
    try {
      setGenerating(true);

      const parsedResponse = JSON.parse(apiResponse);

      const response = await fetch(
        `${config.apiBaseUrl}/api/network/generate-metadata`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            data: parsedResponse,
            prefix: metadataPrefix,
            max_depth: 10,
          }),
        }
      );

      const result = await response.json();

      if (result.status === "success") {
        setGeneratedMetadata(result.metadata);
        addNotification({
          type: "success",
          title: "✅ Metadata Generated",
          message: `Generated ${result.field_count} field mappings`,
          duration: 5000,
        });
      } else {
        throw new Error(result.message || "Failed to generate metadata");
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Metadata Generation Failed",
        message: error.message,
        duration: 5000,
      });
    } finally {
      setGenerating(false);
    }
  };

  // Extract Fields from Response
  const handleExtractFields = async () => {
    try {
      setExtractingFields(true);

      const parsedResponse = JSON.parse(responseData);
      const parsedMappings = JSON.parse(fieldMappings);

      const response = await fetch(
        `${config.apiBaseUrl}/api/network/extract-fields`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            response_data: parsedResponse,
            field_mappings: parsedMappings,
          }),
        }
      );

      const result = await response.json();

      if (result.status === "success") {
        setExtractedFields(result.extracted_fields);
        addNotification({
          type: "success",
          title: "✅ Fields Extracted",
          message: `Extracted ${result.field_count} fields`,
          duration: 5000,
        });
      } else {
        throw new Error(result.message || "Failed to extract fields");
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Field Extraction Failed",
        message: error.message,
        duration: 5000,
      });
    } finally {
      setExtractingFields(false);
    }
  };

  // Validate Response
  const handleValidate = async () => {
    try {
      setValidating(true);

      const parsedResponse = JSON.parse(validationResponse);
      const parsedMetadata = JSON.parse(validationMetadata);

      const response = await fetch(
        `${config.apiBaseUrl}/api/network/validate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            response_data: parsedResponse,
            metadata: parsedMetadata,
          }),
        }
      );

      const result = await response.json();

      if (result.status === "success") {
        setValidationResult(result.validation);
        addNotification({
          type: result.validation.validation_passed ? "success" : "warning",
          title: result.validation.validation_passed
            ? "✅ Validation Passed"
            : "⚠️ Validation Issues Found",
          message: `${result.validation.fields_found}/${result.validation.total_fields} fields found`,
          duration: 5000,
        });
      } else {
        throw new Error(result.message || "Failed to validate");
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Validation Failed",
        message: error.message,
        duration: 5000,
      });
    } finally {
      setValidating(false);
    }
  };

  // Compare Environments
  const handleCompare = async () => {
    try {
      setComparing(true);

      const parsedDev = JSON.parse(devExtraction);
      const parsedStaging = JSON.parse(stagingExtraction);
      const parsedProd = JSON.parse(prodExtraction);

      const response = await fetch(
        `${config.apiBaseUrl}/api/network/compare-environments`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            extractions: {
              dev: parsedDev,
              staging: parsedStaging,
              prod: parsedProd,
            },
          }),
        }
      );

      const result = await response.json();

      if (result.status === "success") {
        setComparisonResult(result.comparison);
        addNotification({
          type: "info",
          title: "📊 Comparison Complete",
          message: `Found ${result.comparison.summary.fields_with_differences} differences`,
          duration: 5000,
        });
      } else {
        throw new Error(result.message || "Failed to compare");
      }
    } catch (error: any) {
      addNotification({
        type: "error",
        title: "❌ Comparison Failed",
        message: error.message,
        duration: 5000,
      });
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="network-tab">
      {/* Section Tabs */}
      <div className="network-section-tabs">
        <button
          className={`network-section-tab ${
            activeSection === "metadata" ? "active" : ""
          }`}
          onClick={() => setActiveSection("metadata")}
        >
          🔍 Generate Metadata
        </button>
        <button
          className={`network-section-tab ${
            activeSection === "extract" ? "active" : ""
          }`}
          onClick={() => setActiveSection("extract")}
        >
          📦 Extract Fields
        </button>
        <button
          className={`network-section-tab ${
            activeSection === "validate" ? "active" : ""
          }`}
          onClick={() => setActiveSection("validate")}
        >
          ✅ Validate Response
        </button>
        <button
          className={`network-section-tab ${
            activeSection === "compare" ? "active" : ""
          }`}
          onClick={() => setActiveSection("compare")}
        >
          📊 Compare Environments
        </button>
      </div>

      {/* Section Content */}
      <div className="network-section-content">
        {/* Metadata Generation Section */}
        {activeSection === "metadata" && (
          <div className="network-section">
            <h3>🔍 Auto-Generate Metadata from API Response</h3>
            <p className="network-section-description">
              Select an intercepted API from the dropdown or manually paste a
              response to generate field mappings.
            </p>

            {/* ✅ NEW: API Selection UI */}
            <div className="network-api-selection">
              <div className="network-form-group">
                <label>
                  Intercepted APIs ({interceptedApis.length}):
                  <button
                    onClick={loadInterceptedApis}
                    disabled={loadingApis}
                    className="network-button-inline"
                    style={{ marginLeft: "10px" }}
                  >
                    {loadingApis ? "⏳" : "🔄"} Refresh
                  </button>
                  {interceptedApis.length > 0 && (
                    <button
                      onClick={handleClearApis}
                      className="network-button-inline"
                      style={{ marginLeft: "10px" }}
                    >
                      🗑️ Clear All
                    </button>
                  )}
                </label>
              </div>

              {/* ✅ NEW: Filters */}
              {interceptedApis.length > 0 && (
                <div
                  className="network-filters"
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 2fr 1fr",
                    gap: "10px",
                    marginBottom: "15px",
                    padding: "15px",
                    background: "#f8f9fa",
                    borderRadius: "8px",
                    border: "1px solid #dee2e6",
                  }}
                >
                  <div className="network-form-group" style={{ margin: 0 }}>
                    <label style={{ fontSize: "12px", fontWeight: "600" }}>
                      Method:
                    </label>
                    <select
                      value={methodFilter}
                      onChange={(e) => setMethodFilter(e.target.value)}
                      className="network-select"
                      style={{ fontSize: "13px" }}
                    >
                      <option value="ALL">All Methods</option>
                      {uniqueMethods.map((method) => (
                        <option key={method} value={method}>
                          {method}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="network-form-group" style={{ margin: 0 }}>
                    <label style={{ fontSize: "12px", fontWeight: "600" }}>
                      URL Pattern:
                    </label>
                    <input
                      type="text"
                      value={urlFilter}
                      onChange={(e) => setUrlFilter(e.target.value)}
                      placeholder="Filter by URL (e.g., /api/settings)"
                      className="network-input"
                      style={{ fontSize: "13px" }}
                    />
                  </div>

                  <div className="network-form-group" style={{ margin: 0 }}>
                    <label style={{ fontSize: "12px", fontWeight: "600" }}>
                      Status Code:
                    </label>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="network-select"
                      style={{ fontSize: "13px" }}
                    >
                      <option value="ALL">All Status</option>
                      <option value="2xx">2xx (Success)</option>
                      <option value="3xx">3xx (Redirect)</option>
                      <option value="4xx">4xx (Client Error)</option>
                      <option value="5xx">5xx (Server Error)</option>
                    </select>
                  </div>
                </div>
              )}

              <div className="network-form-group">
                <label>
                  {filteredApis.length !== interceptedApis.length && (
                    <span style={{ color: "#0066cc", fontWeight: "600" }}>
                      Showing {filteredApis.length} of {interceptedApis.length}{" "}
                      APIs
                    </span>
                  )}
                  {filteredApis.length === interceptedApis.length && (
                    <span>Select an API:</span>
                  )}
                </label>

                {/* ✅ NEW: Custom API list with delete buttons */}
                {filteredApis.length === 0 ? (
                  <div className="network-api-list-empty">
                    No APIs match the filters
                  </div>
                ) : (
                  <div className="network-api-list">
                    {filteredApis.map((api) => (
                      <div
                        key={api.id}
                        className={`network-api-item ${
                          selectedApiId === api.id ? "selected" : ""
                        }`}
                        onClick={() => handleApiSelection(api.id)}
                      >
                        <div className="network-api-item-content">
                          <div className="network-api-item-header">
                            <span
                              className={`network-api-method method-${api.method.toLowerCase()}`}
                            >
                              {api.method}
                            </span>
                            <span
                              className={`network-api-status status-${Math.floor(
                                api.status / 100
                              )}xx`}
                            >
                              {api.status}
                            </span>
                          </div>
                          <div className="network-api-item-url" title={api.url}>
                            {api.url}
                          </div>
                          {api.page_url && (
                            <div
                              className="network-api-item-page"
                              title={api.page_url}
                            >
                              📄 {api.page_url}
                            </div>
                          )}
                        </div>
                        <button
                          className="network-api-delete-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteApi(api.id);
                          }}
                          title="Delete this API"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="network-form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={showManualInput}
                    onChange={(e) => setShowManualInput(e.target.checked)}
                    style={{ marginRight: "8px" }}
                  />
                  Or manually paste API response
                </label>
              </div>
            </div>

            {/* ✅ Manual Input (optional) */}
            {showManualInput && (
              <>
                <div className="network-form-group">
                  <label>API Response JSON:</label>
                  <textarea
                    value={apiResponse}
                    onChange={(e) => setApiResponse(e.target.value)}
                    placeholder='{"data": {"dealerName": "ABC Motors", "id": "123"}}'
                    rows={10}
                    className="network-textarea"
                  />
                </div>
                <button
                  onClick={handleAddManualApi}
                  disabled={!apiResponse}
                  className="network-button secondary"
                  style={{ marginBottom: "20px" }}
                >
                  ➕ Add to Intercepted APIs
                </button>
              </>
            )}

            {/* ✅ Show selected API response */}
            {selectedApiId && !showManualInput && (
              <div className="network-form-group">
                <label>Selected API Response:</label>
                <pre className="network-json" style={{ maxHeight: "300px" }}>
                  {apiResponse}
                </pre>
              </div>
            )}

            <div className="network-form-group">
              <label>Prefix (default: "data"):</label>
              <input
                type="text"
                value={metadataPrefix}
                onChange={(e) => setMetadataPrefix(e.target.value)}
                placeholder="data"
                className="network-input"
              />
            </div>

            <button
              onClick={handleGenerateMetadata}
              disabled={generating || !apiResponse}
              className="network-button primary"
            >
              {generating ? "Generating..." : "Generate Metadata"}
            </button>

            {generatedMetadata && (
              <div className="network-result">
                <h4>
                  Generated Metadata ({Object.keys(generatedMetadata).length}{" "}
                  fields):
                </h4>
                <pre className="network-json">
                  {JSON.stringify(generatedMetadata, null, 2)}
                </pre>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(
                      JSON.stringify(generatedMetadata, null, 2)
                    );
                    addNotification({
                      type: "success",
                      title: "📋 Copied",
                      message: "Metadata copied to clipboard",
                      duration: 3000,
                    });
                  }}
                  className="network-button secondary"
                >
                  📋 Copy to Clipboard
                </button>
              </div>
            )}
          </div>
        )}

        {/* Field Extraction Section */}
        {activeSection === "extract" && (
          <div className="network-section">
            <h3>📦 Extract Fields from API Response</h3>
            <p className="network-section-description">
              Extract specific fields from an API response using metadata
              mappings.
            </p>

            <div className="network-form-group">
              <label>API Response JSON:</label>
              <textarea
                value={responseData}
                onChange={(e) => setResponseData(e.target.value)}
                placeholder='{"data": {"dealerName": "ABC Motors"}}'
                rows={8}
                className="network-textarea"
              />
            </div>

            <div className="network-form-group">
              <label>Field Mappings (Metadata):</label>
              <textarea
                value={fieldMappings}
                onChange={(e) => setFieldMappings(e.target.value)}
                placeholder='{"dealerName": {"api_path": "data.dealerName", "type": "string", "display_name": "Dealer Name"}}'
                rows={8}
                className="network-textarea"
              />
            </div>

            <button
              onClick={handleExtractFields}
              disabled={extractingFields || !responseData || !fieldMappings}
              className="network-button primary"
            >
              {extractingFields ? "Extracting..." : "Extract Fields"}
            </button>

            {extractedFields && (
              <div className="network-result">
                <h4>Extracted Fields:</h4>
                <div className="network-fields-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Field ID</th>
                        <th>Display Name</th>
                        <th>Type</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(extractedFields).map(
                        ([fieldId, fieldData]: [string, any]) => (
                          <tr key={fieldId}>
                            <td>
                              <code>{fieldId}</code>
                            </td>
                            <td>{fieldData.display_name}</td>
                            <td>
                              <span className="network-type-badge">
                                {fieldData.type}
                              </span>
                            </td>
                            <td>
                              <code className="network-value">
                                {JSON.stringify(fieldData.value)}
                              </code>
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Validation Section */}
        {activeSection === "validate" && (
          <div className="network-section">
            <h3>✅ Validate API Response</h3>
            <p className="network-section-description">
              Validate an API response against expected metadata schema to check
              for missing fields or type mismatches.
            </p>

            <div className="network-form-group">
              <label>API Response JSON:</label>
              <textarea
                value={validationResponse}
                onChange={(e) => setValidationResponse(e.target.value)}
                placeholder='{"data": {"dealerName": "ABC Motors"}}'
                rows={8}
                className="network-textarea"
              />
            </div>

            <div className="network-form-group">
              <label>Expected Metadata Schema:</label>
              <textarea
                value={validationMetadata}
                onChange={(e) => setValidationMetadata(e.target.value)}
                placeholder='{"dealerName": {"api_path": "data.dealerName", "type": "string"}}'
                rows={8}
                className="network-textarea"
              />
            </div>

            <button
              onClick={handleValidate}
              disabled={
                validating || !validationResponse || !validationMetadata
              }
              className="network-button primary"
            >
              {validating ? "Validating..." : "Validate Response"}
            </button>

            {validationResult && (
              <div className="network-result">
                <h4>
                  Validation Result:{" "}
                  {validationResult.validation_passed ? (
                    <span className="network-status-success">✅ PASSED</span>
                  ) : (
                    <span className="network-status-error">❌ FAILED</span>
                  )}
                </h4>

                <div className="network-validation-summary">
                  <div className="network-stat">
                    <span className="network-stat-label">Total Fields:</span>
                    <span className="network-stat-value">
                      {validationResult.total_fields}
                    </span>
                  </div>
                  <div className="network-stat">
                    <span className="network-stat-label">Fields Found:</span>
                    <span className="network-stat-value network-stat-success">
                      {validationResult.fields_found}
                    </span>
                  </div>
                  <div className="network-stat">
                    <span className="network-stat-label">Fields Missing:</span>
                    <span className="network-stat-value network-stat-error">
                      {validationResult.fields_missing}
                    </span>
                  </div>
                  <div className="network-stat">
                    <span className="network-stat-label">Type Mismatches:</span>
                    <span className="network-stat-value network-stat-warning">
                      {validationResult.type_mismatches}
                    </span>
                  </div>
                </div>

                {validationResult.missing_fields.length > 0 && (
                  <div className="network-validation-issues">
                    <h5>Missing Fields:</h5>
                    <ul>
                      {validationResult.missing_fields.map((field: any) => (
                        <li key={field.field_id}>
                          <code>{field.field_id}</code> ({field.expected_type})
                          - Path: {field.api_path}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {validationResult.type_mismatch_details.length > 0 && (
                  <div className="network-validation-issues">
                    <h5>Type Mismatches:</h5>
                    <ul>
                      {validationResult.type_mismatch_details.map(
                        (field: any) => (
                          <li key={field.field_id}>
                            <code>{field.field_id}</code> - Expected:{" "}
                            {field.expected_type}, Got: {field.actual_type}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Environment Comparison Section */}
        {activeSection === "compare" && (
          <div className="network-section">
            <h3>📊 Compare API Responses Across Environments</h3>
            <p className="network-section-description">
              Compare the same API response from different environments (dev,
              staging, prod) to identify differences.
            </p>

            <div className="network-form-group">
              <label>Dev Environment Extraction:</label>
              <textarea
                value={devExtraction}
                onChange={(e) => setDevExtraction(e.target.value)}
                placeholder='{"extracted_fields": {...}}'
                rows={6}
                className="network-textarea"
              />
            </div>

            <div className="network-form-group">
              <label>Staging Environment Extraction:</label>
              <textarea
                value={stagingExtraction}
                onChange={(e) => setStagingExtraction(e.target.value)}
                placeholder='{"extracted_fields": {...}}'
                rows={6}
                className="network-textarea"
              />
            </div>

            <div className="network-form-group">
              <label>Prod Environment Extraction:</label>
              <textarea
                value={prodExtraction}
                onChange={(e) => setProdExtraction(e.target.value)}
                placeholder='{"extracted_fields": {...}}'
                rows={6}
                className="network-textarea"
              />
            </div>

            <button
              onClick={handleCompare}
              disabled={
                comparing ||
                !devExtraction ||
                !stagingExtraction ||
                !prodExtraction
              }
              className="network-button primary"
            >
              {comparing ? "Comparing..." : "Compare Environments"}
            </button>

            {comparisonResult && (
              <div className="network-result">
                <h4>Comparison Summary:</h4>

                <div className="network-validation-summary">
                  <div className="network-stat">
                    <span className="network-stat-label">Total Fields:</span>
                    <span className="network-stat-value">
                      {comparisonResult.summary.total_fields}
                    </span>
                  </div>
                  <div className="network-stat">
                    <span className="network-stat-label">Identical:</span>
                    <span className="network-stat-value network-stat-success">
                      {comparisonResult.summary.identical_fields}
                    </span>
                  </div>
                  <div className="network-stat">
                    <span className="network-stat-label">Differences:</span>
                    <span className="network-stat-value network-stat-warning">
                      {comparisonResult.summary.fields_with_differences}
                    </span>
                  </div>
                </div>

                {comparisonResult.differences.length > 0 && (
                  <div className="network-comparison-differences">
                    <h5>Fields with Differences:</h5>
                    <table>
                      <thead>
                        <tr>
                          <th>Field ID</th>
                          <th>Dev</th>
                          <th>Staging</th>
                          <th>Prod</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonResult.differences.map((diff: any) => (
                          <tr key={diff.field_id}>
                            <td>
                              <code>{diff.field_id}</code>
                            </td>
                            <td>
                              <code className="network-value">
                                {JSON.stringify(diff.values.dev)}
                              </code>
                            </td>
                            <td>
                              <code className="network-value">
                                {JSON.stringify(diff.values.staging)}
                              </code>
                            </td>
                            <td>
                              <code className="network-value">
                                {JSON.stringify(diff.values.prod)}
                              </code>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ✅ Memoize to prevent unnecessary re-renders
export const NetworkTab = React.memo(NetworkTabComponent);
