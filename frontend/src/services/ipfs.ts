import { create } from 'ipfs-http-client';

// Configure IPFS client
const ipfs = create({
  host: 'localhost',
  port: 5001,
  protocol: 'http',
});

export interface IPFSFile {
  path: string;
  hash: string;
  size: number;
}

export const ipfsService = {
  // Upload file to IPFS
  uploadFile: async (file: File): Promise<string> => {
    try {
      const added = await ipfs.add(file);
      return added.path;
    } catch (error) {
      console.error('Error uploading to IPFS:', error);
      throw new Error('Failed to upload file to IPFS');
    }
  },

  // Upload JSON data to IPFS
  uploadJSON: async (data: any): Promise<string> => {
    try {
      const jsonString = JSON.stringify(data);
      const added = await ipfs.add(jsonString);
      return added.path;
    } catch (error) {
      console.error('Error uploading JSON to IPFS:', error);
      throw new Error('Failed to upload JSON to IPFS');
    }
  },

  // Get file from IPFS
  getFile: async (hash: string): Promise<Uint8Array> => {
    try {
      const chunks = [];
      for await (const chunk of ipfs.cat(hash)) {
        chunks.push(chunk);
      }
      
      // Concatenate chunks
      const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
      const result = new Uint8Array(totalLength);
      let offset = 0;
      
      for (const chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
      }
      
      return result;
    } catch (error) {
      console.error('Error getting file from IPFS:', error);
      throw new Error('Failed to get file from IPFS');
    }
  },

  // Get JSON data from IPFS
  getJSON: async (hash: string): Promise<any> => {
    try {
      const file = await ipfsService.getFile(hash);
      const jsonString = new TextDecoder().decode(file);
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Error getting JSON from IPFS:', error);
      throw new Error('Failed to get JSON from IPFS');
    }
  },

  // Pin file to IPFS
  pinFile: async (hash: string): Promise<void> => {
    try {
      await ipfs.pin.add(hash);
    } catch (error) {
      console.error('Error pinning file to IPFS:', error);
      throw new Error('Failed to pin file to IPFS');
    }
  },

  // Unpin file from IPFS
  unpinFile: async (hash: string): Promise<void> => {
    try {
      await ipfs.pin.rm(hash);
    } catch (error) {
      console.error('Error unpinning file from IPFS:', error);
      throw new Error('Failed to unpin file from IPFS');
    }
  },

  // Get IPFS node status
  getNodeStatus: async (): Promise<any> => {
    try {
      const id = await ipfs.id();
      return id;
    } catch (error) {
      console.error('Error getting IPFS node status:', error);
      throw new Error('Failed to get IPFS node status');
    }
  },
};

export default ipfsService;
