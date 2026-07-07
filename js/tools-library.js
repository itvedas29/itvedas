/**
 * ITVedas Tools Library
 * Reusable tool components and utilities
 */

class ToolsLibrary {
  /**
   * Create a subnet calculator tool
   */
  static createSubnetCalculator() {
    return {
      id: 'subnet-calculator',
      name: 'Subnet Calculator',
      category: 'Networking',
      description: 'Calculate subnets, host ranges, and network information from CIDR notation.',
      icon: '🔢',
      usage: 'Enter an IP address with CIDR notation (e.g., 192.168.1.0/24)',
      render: () => `
        <div class="tool-form">
          <input type="text" id="subnetInput" placeholder="192.168.1.0/24" class="tool-input">
          <button onclick="ToolsLibrary.calculateSubnet()" class="btn">Calculate</button>
        </div>
        <div id="subnetResult" class="tool-result" style="display: none;"></div>
      `,
      calculate: (input) => {
        // Parse CIDR
        const [ip, cidr] = input.split('/');
        const octets = ip.split('.').map(Number);
        const cidrNum = parseInt(cidr);

        // Calculate network bits and host bits
        const hostBits = 32 - cidrNum;
        const totalHosts = Math.pow(2, hostBits) - 2;

        // Calculate network and broadcast
        const ipNum = (octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3];
        const mask = (0xFFFFFFFF << hostBits) >>> 0;
        const networkNum = ipNum & mask;
        const broadcastNum = networkNum | (~mask >>> 0);

        // Convert back to IP
        const formatIP = (num) => {
          return [
            (num >>> 24) & 0xFF,
            (num >>> 16) & 0xFF,
            (num >>> 8) & 0xFF,
            num & 0xFF
          ].join('.');
        };

        return {
          cidr: `${ip}/${cidr}`,
          network: formatIP(networkNum),
          broadcast: formatIP(broadcastNum),
          firstHost: formatIP(networkNum + 1),
          lastHost: formatIP(broadcastNum - 1),
          totalHosts: totalHosts,
          subnetMask: formatIP(mask),
          wildcard: formatIP(~mask >>> 0)
        };
      }
    };
  }

  /**
   * Create a password generator tool
   */
  static createPasswordGenerator() {
    return {
      id: 'password-generator',
      name: 'Password Generator',
      category: 'Security',
      description: 'Generate strong, random passwords with customizable options.',
      icon: '🔐',
      render: () => `
        <div class="tool-form">
          <div class="form-group">
            <label>Password Length:</label>
            <input type="range" id="passLength" min="8" max="32" value="16" class="tool-slider">
            <span id="lengthDisplay">16</span>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" id="includeNumbers" checked> Numbers (0-9)
            </label>
            <label>
              <input type="checkbox" id="includeSymbols" checked> Symbols (!@#$%)
            </label>
            <label>
              <input type="checkbox" id="includeLowercase" checked> Lowercase (a-z)
            </label>
            <label>
              <input type="checkbox" id="includeUppercase" checked> Uppercase (A-Z)
            </label>
          </div>
          <button onclick="ToolsLibrary.generatePassword()" class="btn">Generate</button>
        </div>
        <div id="passResult" class="tool-result" style="display: none;">
          <input type="text" id="generatedPass" readonly class="tool-input">
          <button onclick="ToolsLibrary.copyToClipboard('generatedPass')" class="btn btn-secondary">Copy</button>
        </div>
      `,
      generate: (length, options) => {
        const chars = {
          numbers: '0123456789',
          lowercase: 'abcdefghijklmnopqrstuvwxyz',
          uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
          symbols: '!@#$%^&*()_+-=[]{}|;:,.<>?'
        };

        let pool = '';
        if (options.numbers) pool += chars.numbers;
        if (options.lowercase) pool += chars.lowercase;
        if (options.uppercase) pool += chars.uppercase;
        if (options.symbols) pool += chars.symbols;

        let password = '';
        for (let i = 0; i < length; i++) {
          password += pool.charAt(Math.floor(Math.random() * pool.length));
        }
        return password;
      }
    };
  }

  /**
   * Create a JSON formatter tool
   */
  static createJsonFormatter() {
    return {
      id: 'json-formatter',
      name: 'JSON Formatter',
      category: 'Developer',
      description: 'Format, validate, and beautify JSON data.',
      icon: '{}',
      render: () => `
        <div class="tool-form">
          <textarea id="jsonInput" class="tool-textarea" placeholder="Paste JSON here..."></textarea>
          <div class="form-group">
            <button onclick="ToolsLibrary.formatJson()" class="btn">Format</button>
            <button onclick="ToolsLibrary.minifyJson()" class="btn btn-secondary">Minify</button>
            <button onclick="ToolsLibrary.validateJson()" class="btn btn-secondary">Validate</button>
          </div>
        </div>
        <div id="jsonResult" class="tool-result" style="display: none;">
          <pre id="jsonOutput"></pre>
          <button onclick="ToolsLibrary.copyToClipboard('jsonOutput')" class="btn btn-secondary">Copy</button>
        </div>
      `,
      format: (json) => {
        try {
          const parsed = JSON.parse(json);
          return JSON.stringify(parsed, null, 2);
        } catch (e) {
          return `Error: ${e.message}`;
        }
      },
      validate: (json) => {
        try {
          JSON.parse(json);
          return { valid: true, message: '✓ Valid JSON' };
        } catch (e) {
          return { valid: false, message: `✗ Invalid: ${e.message}` };
        }
      }
    };
  }

  /**
   * Create a UUID generator tool
   */
  static createUuidGenerator() {
    return {
      id: 'uuid-generator',
      name: 'UUID Generator',
      category: 'Developer',
      description: 'Generate unique identifier (UUID v4) for your projects.',
      icon: '🆔',
      render: () => `
        <div class="tool-form">
          <label>Number of UUIDs:</label>
          <input type="number" id="uuidCount" min="1" max="100" value="1" class="tool-input">
          <button onclick="ToolsLibrary.generateUuids()" class="btn">Generate</button>
        </div>
        <div id="uuidResult" class="tool-result" style="display: none;">
          <textarea id="uuidOutput" readonly class="tool-textarea"></textarea>
          <button onclick="ToolsLibrary.copyToClipboard('uuidOutput')" class="btn btn-secondary">Copy All</button>
        </div>
      `,
      generateUuid: () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      }
    };
  }

  /**
   * Create a base64 encoder/decoder tool
   */
  static createBase64Tool() {
    return {
      id: 'base64-encoder',
      name: 'Base64 Encoder/Decoder',
      category: 'Developer',
      description: 'Encode and decode Base64 strings.',
      icon: '🔤',
      render: () => `
        <div class="tool-form">
          <textarea id="base64Input" class="tool-textarea" placeholder="Enter text to encode or Base64 to decode..."></textarea>
          <div class="form-group">
            <button onclick="ToolsLibrary.encodeBase64()" class="btn">Encode to Base64</button>
            <button onclick="ToolsLibrary.decodeBase64()" class="btn btn-secondary">Decode from Base64</button>
          </div>
        </div>
        <div id="base64Result" class="tool-result" style="display: none;">
          <textarea id="base64Output" readonly class="tool-textarea"></textarea>
          <button onclick="ToolsLibrary.copyToClipboard('base64Output')" class="btn btn-secondary">Copy</button>
        </div>
      `,
      encode: (str) => btoa(unescape(encodeURIComponent(str))),
      decode: (str) => {
        try {
          return decodeURIComponent(escape(atob(str)));
        } catch (e) {
          return `Error: Invalid Base64`;
        }
      }
    };
  }

  /**
   * Copy text to clipboard
   */
  static copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    element.select();
    document.execCommand('copy');

    // Show feedback
    const originalText = 'Copy';
    const btn = event.target;
    btn.textContent = 'Copied!';
    setTimeout(() => {
      btn.textContent = originalText;
    }, 2000);
  }

  /**
   * Format JSON (callable)
   */
  static formatJson() {
    const input = document.getElementById('jsonInput').value;
    const result = this.createJsonFormatter().format(input);
    const output = document.getElementById('jsonOutput');
    output.textContent = result;
    document.getElementById('jsonResult').style.display = 'block';
  }

  /**
   * Calculate subnet (callable)
   */
  static calculateSubnet() {
    const input = document.getElementById('subnetInput').value;
    try {
      const result = this.createSubnetCalculator().calculate(input);
      const html = `
        <strong>Subnet Information</strong>
        <p>Network: ${result.network}</p>
        <p>Broadcast: ${result.broadcast}</p>
        <p>First Host: ${result.firstHost}</p>
        <p>Last Host: ${result.lastHost}</p>
        <p>Total Hosts: ${result.totalHosts}</p>
        <p>Subnet Mask: ${result.subnetMask}</p>
      `;
      document.getElementById('subnetResult').innerHTML = html;
      document.getElementById('subnetResult').style.display = 'block';
    } catch (e) {
      alert('Invalid CIDR notation. Use format: 192.168.1.0/24');
    }
  }

  /**
   * Generate password (callable)
   */
  static generatePassword() {
    const length = parseInt(document.getElementById('passLength').value);
    const options = {
      numbers: document.getElementById('includeNumbers').checked,
      lowercase: document.getElementById('includeLowercase').checked,
      uppercase: document.getElementById('includeUppercase').checked,
      symbols: document.getElementById('includeSymbols').checked
    };

    const password = this.createPasswordGenerator().generate(length, options);
    document.getElementById('generatedPass').value = password;
    document.getElementById('passResult').style.display = 'block';
  }

  /**
   * Generate UUIDs (callable)
   */
  static generateUuids() {
    const count = parseInt(document.getElementById('uuidCount').value);
    const uuids = [];
    for (let i = 0; i < count; i++) {
      uuids.push(this.createUuidGenerator().generateUuid());
    }
    document.getElementById('uuidOutput').value = uuids.join('\n');
    document.getElementById('uuidResult').style.display = 'block';
  }

  /**
   * Encode Base64 (callable)
   */
  static encodeBase64() {
    const input = document.getElementById('base64Input').value;
    const output = this.createBase64Tool().encode(input);
    document.getElementById('base64Output').value = output;
    document.getElementById('base64Result').style.display = 'block';
  }

  /**
   * Decode Base64 (callable)
   */
  static decodeBase64() {
    const input = document.getElementById('base64Input').value;
    const output = this.createBase64Tool().decode(input);
    document.getElementById('base64Output').value = output;
    document.getElementById('base64Result').style.display = 'block';
  }

  /**
   * Get all available tools
   */
  static getAllTools() {
    return [
      this.createSubnetCalculator(),
      this.createPasswordGenerator(),
      this.createJsonFormatter(),
      this.createUuidGenerator(),
      this.createBase64Tool()
    ];
  }
}

// Update length display for password generator
document.addEventListener('DOMContentLoaded', () => {
  const lengthInput = document.getElementById('passLength');
  if (lengthInput) {
    lengthInput.addEventListener('input', (e) => {
      document.getElementById('lengthDisplay').textContent = e.target.value;
    });
  }
});

window.ToolsLibrary = ToolsLibrary;
